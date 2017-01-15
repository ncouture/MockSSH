#!/usr/bin/env hy

; example use of the HyLang MockSSH DSL (mocksshy)

(import MockSSH)
(require mocksshy.language)

; define parameters for printing
(setv users {"testuser" "1234"})
(setv host "127.0.0.1")
(setv port 2222)

; print server and connection info
(print (.format "Starting SSH server port {1} of {0}..." host port))
(print (.format "\nUsername: {0}\nPassword: {1}"
                (name (first (first (.items users))))
                (second (first (.items users)))))

; start server
(mock-ssh :users users
          :host host
          :port port
          :prompt "hostname>"
          :commands [
  (command :name "en"
           :type "prompt"
           :output "Password: "
           :required-input "1234"
           :on-success ["prompt" "hostname#"]
           :on-failure ["write" "Pass is 1234..."])
  (command :name "ls"
           :type "output"
           :args ["-1"]
           :on-success ["write" "bin\nREADME.txt"]
           :on-failure ["write" "MockSSH: supported usage: ls -1"])])
