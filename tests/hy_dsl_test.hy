(import time)
(import paramiko)
(import pytest)
(import MockSSH)
(require mocksshy.language *)

(defn recv-all [channel]
  (while (not (.recv_ready channel))
    (time.sleep 0.1))
  (setv stdout b"")
  (while (.recv_ready channel)
    (setv stdout (+ stdout (.recv channel 1024))))
  (.decode stdout "utf-8"))

(defn test-mock-hy-dsl []
  "Test the MockSSH DSL (mocksshy) from HyLang."
  (setv users {"testuser" "1234"})
  (setv commands [
    (command :name "ls"
             :type "output"
             :args ["-1"]
             :on-success ["write" "file1\nfile2"]
             :on-failure ["write" "usage: ls -1"])
    (command :name "en"
             :type "prompt"
             :output "Password: "
             :required-input "1234"
             :on-success ["prompt" "hostname#"]
             :on-failure ["write" "Access denied"])])

  ;; Use port 0 to let the OS assign an available port
  (setv server (MockSSH.startThreadedServer commands
                                            :prompt "hostname>"
                                            :port 0
                                            #** users))
  (setv port (. (.getHost server) port))
  (setv ssh (paramiko.SSHClient))
  (try
    (.set_missing_host_key_policy ssh (paramiko.AutoAddPolicy))
    
    ;; Retry connection a few times
    (setv connected False)
    (for [i (range 10)]
      (try
        (.connect ssh "127.0.0.1" 
                  :username "testuser" 
                  :password "1234" 
                  :port port 
                  :allow_agent False 
                  :look_for_keys False 
                  :timeout 10)
        (setv connected True)
        (break)
        (catch [e Exception]
          (time.sleep 0.5))))
    
    (if (not connected)
      (raise (Exception "Failed to connect to MockSSH server"))
      None)

    (setv channel (.invoke_shell ssh))
    (recv-all channel) ; Clear initial prompt

    ;; Test 'ls -1' command
    (.send channel "ls -1\n")
    (setv output (recv-all channel))
    (assert (in "file1" output))
    (assert (in "file2" output))

    ;; Test 'en' command with prompting
    (.send channel "en\n")
    (setv output (recv-all channel))
    (assert (in "Password: " output))
    
    (.send channel "1234\n")
    (setv output (recv-all channel))
    (assert (in "hostname#" output))

    (finally
      (.close ssh)
      (MockSSH.stopThreadedServer server))))
