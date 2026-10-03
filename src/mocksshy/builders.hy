;; Shared parsing, validation and runtime builders for the command macros
;; defined in mocksshy.language.
(import mocksshy.kwzip [group-map keyword? one])
(import MockSSH)
(import hy.models [Keyword])

(setv COMMAND-KEYS #{"name" "type" "args" "output" "required-input"
                     "on-success" "on-failure"})
(setv COMMAND-TYPES #{"prompt" "output"})


;; --- expansion-time helpers -------------------------------------------

(defn normalize-name [value]
  "Return *value* (string, symbol or keyword model) as a plain string."
  (if (isinstance value Keyword) (. value name) (str value)))

(defn parse-spec [macro-name forms]
  "Group keyword/value *forms* into a dict of single values (default None).
Unknown keys, duplicate keys and a missing :name raise ValueError."
  (setv data (group-map keyword? forms))
  (for [key (list (.keys data))]
    (when (or (not (isinstance key Keyword))
              (not-in (. key name) COMMAND-KEYS))
      (raise (ValueError
               (.format "{}: unknown or misplaced argument {}; expected one of: {}"
                        macro-name
                        (if (isinstance key Keyword) (repr key) "<value without keyword>")
                        (.join ", " (sorted COMMAND-KEYS)))))))
  (setv spec {})
  (for [key COMMAND-KEYS]
    (try
      (setv (get spec key) (one None (.get data (Keyword key) [])))
      (except [TypeError]
        (raise (ValueError (.format "{}: :{} was given more than once"
                                    macro-name key))))))
  (when (is (get spec "name") None)
    (raise (ValueError (.format "{}: missing required :name" macro-name))))
  spec)

(defn command-type [spec]
  "Validated, normalized :type of a `command` spec."
  (setv type (get spec "type"))
  (when (is type None)
    (raise (ValueError
             (.format "command {!r}: missing required :type (one of: {})"
                      (str (get spec "name"))
                      (.join ", " (sorted COMMAND-TYPES))))))
  (setv type-str (normalize-name type))
  (when (not-in type-str COMMAND-TYPES)
    (raise (ValueError
             (.format "command {!r}: unsupported :type {!r} (expected one of: {})"
                      (str (get spec "name")) type-str
                      (.join ", " (sorted COMMAND-TYPES))))))
  type-str)


;; --- runtime helpers ---------------------------------------------------

(defn check-name [name]
  (when (not (isinstance name str))
    (raise (MockSSH.MockSSHError
             (.format "command name must be a string, got {!r}" name))))
  name)

(defn check-callbacks [name label value pairs-only]
  "Validate an :on-success/:on-failure list; return it as [action param] pairs."
  (when (not (isinstance value list))
    (raise (MockSSH.MockSSHError
             (.format "command {!r}: {} argument must be a list, got {!r}"
                      name label value))))
  (if pairs-only
      (when (!= (len value) 2)
        (raise (MockSSH.MockSSHError
                 (.format "command {!r}: {} argument must be a list of exactly two items [action parameter], got {!r}"
                          name label value))))
      (when (% (len value) 2)
        (raise (MockSSH.MockSSHError
                 (.format "command {!r}: {} argument must be an even list of [action parameter ...] items, got {!r}"
                          name label value)))))
  (list (zip (cut value None None 2) (cut value 1 None 2))))

(defn writer [parameter]
  (fn [instance] (.writeln instance parameter)))

(defn prompt-setter [parameter]
  (fn [instance] (setv instance.protocol.prompt parameter)))

(defn make-callbacks [name label pairs actions]
  "Build callbacks from [action parameter] *pairs*; *actions* maps an action
name to a factory taking the parameter."
  (setv callbacks [])
  (for [#(action parameter) pairs]
    (setv factory (.get actions (str action)))
    (when (is factory None)
      (raise (MockSSH.MockSSHError
               (.format "command {!r}: unsupported {} action {!r} (expected one of: {})"
                        name label (str action)
                        (.join ", " (sorted (.keys actions)))))))
    (.append callbacks (factory parameter)))
  callbacks)

(defn build-output-command [name args on-success on-failure]
  (check-name name)
  (setv write-only {"write" writer})
  (MockSSH.ArgumentValidatingCommand
    name
    (make-callbacks name ":on-success"
                    (check-callbacks name ":on-success" on-success False)
                    write-only)
    (make-callbacks name ":on-failure"
                    (check-callbacks name ":on-failure" on-failure False)
                    write-only)
    #* (or args [])))

(defn build-prompting-command [name output required-input on-success on-failure]
  (check-name name)
  (MockSSH.PromptingCommand
    :name name
    :password required-input
    :prompt output
    :success_callbacks (make-callbacks
                         name ":on-success"
                         (check-callbacks name ":on-success" on-success True)
                         {"prompt" prompt-setter})
    :failure_callbacks (make-callbacks
                         name ":on-failure"
                         (check-callbacks name ":on-failure" on-failure True)
                         {"write" writer})))
