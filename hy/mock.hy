(import MockSSH)
(require mockssh.language)


(setv commands [])

(mock-ssh :users {"root" "1234"}
          :host "127.0.0.1"
          :port 2222
          :prompt "mockssh $ "
          :commands [
  (command :name "su"
           :type "prompt"
           :output "Password: "
           :required-input "1234"
           :on-success ["prompt" "mockssh # "]
           :on-failure ["write" "Pass is 1234..."])
  (command :name "ls"
           :type "output"
           :args ["-1"]
           :on-success ["write" "bin\nREADME.txt"]
           :on-failure ["write" "MockSSH: supported usage: ls -1"])])
