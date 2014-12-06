#!/usr/bin/env hy

; example use of the HyLang MockSSH DSL (mocksshy) 

(import MockSSH)
(require mocksshy.language)


(mock-ssh :users {"testuser" "1234"}
          :host "127.0.0.1"
          :port 2222
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
           :on-success ["write" "bin\nREADME.txt" "write" "^H^H^H"]
           :on-failure ["write" "MockSSH: supported usage: ls -1"])])
