(import time)
(import paramiko)
(import pytest)
(import MockSSH)
(require mocksshy.language *)

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

  ;; Use a unique port for this test
  (setv port 2225)
  (setv server (MockSSH.startThreadedServer commands
                                            :prompt "hostname>"
                                            :port port
                                            #** users))
  (setv ssh (paramiko.SSHClient))
  (try
    (.set_missing_host_key_policy ssh (paramiko.AutoAddPolicy))
    
    ;; Wait a bit for server to be ready
    (time.sleep 1)
    
    (.connect ssh "127.0.0.1" 
              :username "testuser" 
              :password "1234" 
              :port port 
              :allow_agent False 
              :look_for_keys False 
              :timeout 10)

    (setv channel (.invoke_shell ssh))
    (time.sleep 1)
    (.recv channel 1024) ; Clear initial prompt

    ;; Test 'ls -1' command
    (.send channel "ls -1\n")
    (time.sleep 1)
    (setv output (.decode (.recv channel 1024) "utf-8"))
    (assert (in "file1" output))
    (assert (in "file2" output))

    ;; Test 'en' command with prompting
    (.send channel "en\n")
    (time.sleep 1)
    (setv output (.decode (.recv channel 1024) "utf-8"))
    (assert (in "Password: " output))
    
    (.send channel "1234\n")
    (time.sleep 1)
    (setv output (.decode (.recv channel 1024) "utf-8"))
    (assert (in "hostname#" output))

    (finally
      (.close ssh)
      (MockSSH.stopThreadedServer server))))
