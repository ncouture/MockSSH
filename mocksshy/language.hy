(import mocksshy.kwzip [group-map keyword? one])
(import MockSSH)
(import hy.models)
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
  (let [data (group-map keyword? forms)
        name (one None (get data :name))
        type (one None (get data :type))
        args (one None (get data :args))
        output (one None (get data :output))
        required-input (one None (get data :required-input))
        on-success (one None (get data :on-success))
        on-failure (one None (get data :on-failure))
        type-str (if (isinstance type hy.models.String) (str type) type)]
    (cond (= type-str "prompt")
          `(prompting-command :name ~name
                              :output ~output
                              :required-input ~required-input
                              :on-success ~on-success
                              :on-failure ~on-failure)
          (= type-str "output")
          `(output-command :name ~name
                           :output ~output
                           :args ~args
                           :on-success ~on-success
                           :on-failure ~on-failure)
          True None)))


(defmacro output-command [#* forms]
  (let [data (group-map keyword? forms)
        name (one None (get data :name))
        output (one None (get data :output))
        args (one None (get data :args))
        required-input (one None (get data :required-input))
        on-success (one None (get data :on-success))
        on-failure (one None (get data :on-failure))]
    `((fn []
        (when (not (and (isinstance ~on-success list)
                        (= (% (len ~on-success) 2) 0)))
          (raise (MockSSH.MockSSHError
                  "on-success argument must be an even list of strings")))
        (when (not (and (isinstance ~on-failure list)
                        (= (% (len ~on-failure) 2) 0)))
          (raise (MockSSH.MockSSHError
                  "on-failure argument must be an even list of strings")))

        (setv success-callbacks [])
        (setv it (iter ~on-success))
        (for [callback (zip it it)]
          (let [on-success-action (get callback 0)
                on-success-parameter (get callback 1)]
            (when (= (str on-success-action) "write")
              (.append success-callbacks
                       (fn [instance]
                         (.writeln instance on-success-parameter))))))

        (setv failure-callbacks [])
        (setv it (iter ~on-failure))
        (for [callback (zip it it)]
          (let [on-failure-action (get callback 0)
                on-failure-parameter (get callback 1)]
            (when (= (str on-failure-action) "write")
              (.append failure-callbacks
                       (fn [instance]
                         (.writeln instance on-failure-parameter))))))

        (MockSSH.ArgumentValidatingCommand ~name success-callbacks failure-callbacks #* ~args)))))


(defmacro prompting-command [#* forms]
  (let [data (group-map keyword? forms)
        name (one None (get data :name))
        output (one None (get data :output))
        required-input (one None (get data :required-input))
        on-success (one None (get data :on-success))
        on-failure (one None (get data :on-failure))]
    `((fn []
        ;; on-success arg example: ["prompt" "hostname# "]
        (when (not (and (isinstance ~on-success list)
                        (= (len ~on-success) 2)))
          (raise (MockSSH.MockSSHError
                  "on-success argument must be a list of two")))

        (setv on-success-action (get ~on-success 0))
        (setv on-success-parameter (get ~on-success 1))

        ;; on-failure arg example: ["write" "Password is 1234!"]
        (when (not (and (isinstance ~on-failure list)
                        (= (len ~on-failure) 2)))
          (raise (MockSSH.MockSSHError
                  "on-failure argument must be a list of at least two")))

        (setv on-failure-action (get ~on-failure 0))
        (setv on-failure-parameter (get ~on-failure 1))

        ;; --- configure commands requirements ---
        (setv success-callbacks [])
        (setv failure-callbacks [])
        (when (= (str on-success-action) "prompt")
          (.append success-callbacks
                   (fn [instance]
                     (setv instance.protocol.prompt on-success-parameter))))

        (when (= (str on-failure-action) "write")
          (.append failure-callbacks
                   (fn [instance]
                     (.writeln instance on-failure-parameter))))

        (MockSSH.PromptingCommand
                #** {"name" ~name
                     "password" ~required-input
                     "prompt" ~output
                     "success_callbacks" success-callbacks
                     "failure_callbacks" failure-callbacks})))))
