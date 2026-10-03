(import mocksshy.kwzip [group-map keyword? one])
(import MockSSH)
(import hy.models)
(import mocksshy.builders :as builders)
(import hy.errors [HyMacroExpansionError])


(defmacro mock-ssh [#* forms]
  (let [data (group-map keyword? forms)
        users (one `{"root" "1234"} (get data :users))
        host (one `"127.0.0.1" (get data :host))
        port (one 2222 (get data :port))
        prompt (one "mockssh $ " (get data :prompt))
        keypath (one "./generated-keys/" (get data :keypath))
        commands (one None (get data :commands))]
    `((fn []
        (MockSSH.runServer ~commands
                           ~prompt
                           ~keypath
                           ~host
                           ~port
                           #** ~users)))))

(defmacro command [#* forms]
  (let [spec (builders.parse-spec "command" forms)
        type (builders.command-type spec)]
    (if (= type "prompt")
        `(prompting-command :name ~(get spec "name")
                            :output ~(get spec "output")
                            :required-input ~(get spec "required-input")
                            :on-success ~(get spec "on-success")
                            :on-failure ~(get spec "on-failure"))
        `(output-command :name ~(get spec "name")
                         :args ~(get spec "args")
                         :on-success ~(get spec "on-success")
                         :on-failure ~(get spec "on-failure")))))


(defmacro output-command [#* forms]
  (let [spec (builders.parse-spec "output-command" forms)]
    `(.build-output-command (hy.I "mocksshy.builders")
       ~(get spec "name")
       ~(get spec "args")
       ~(get spec "on-success")
       ~(get spec "on-failure"))))


(defmacro prompting-command [#* forms]
  (let [spec (builders.parse-spec "prompting-command" forms)]
    `(.build-prompting-command (hy.I "mocksshy.builders")
       ~(get spec "name")
       ~(get spec "output")
       ~(get spec "required-input")
       ~(get spec "on-success")
       ~(get spec "on-failure"))))
