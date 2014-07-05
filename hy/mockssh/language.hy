(import [kwzip [group-map keyword? one]])


(defmacro define [variables &rest body]
  "Kinda like let"
  (import [hy [HyList]])
  (setv macroed_variables [])
  (if (not (isinstance variables HyList))
    (macro-error variables "define lexical context must be a list"))
  (for* [variable variables]
    (if (isinstance variable HyList)
      (do (if (!= (len variable) 2)
            (macro-error variable "define variable assignments must contain two items"))
            (.append macroed-variables `(setv ~(get variable 0) ~(get variable 1))))
      (.append macroed-variables `(setv ~variable None))))
  `(do
     ~@macroed-variables
     ~@body))


(defmacro mock-ssh [&rest forms]                    
  (define [[data (group-map keyword? forms)]
           [users
            (one `{"root" "1234"}
                 (:users data))]
           [host 
            (one `"127.0.0.1"
                 (:host data))]
           [port
            (one `2222 
                 (:port data))]
           [prompt 
            (one `"mockssh $ "
                 (:prompt data))]
           [keypath 
            (one `"." 
                 (:keypath data))]
           [commands (one `nil (:commands data))]]
    `((fn []
        (apply MockSSH.runServer [~commands 
                                  (bytes ~prompt)
                                  ~keypath
                                  (bytes ~host)
                                  ~port] ~users)))))


(defmacro command [&rest forms]
  (define [[data (group-map keyword? forms)]
           [name (one `nil (:name data))]
           [type (one `nil (:type data))]
           [args (one `nil (:args data))]
           [output (one `nil (:output data))]
           [required-input (one `nil (:required-input data))]
           [on-success (one `nil (:on-success data))]
           [on-failure (one `nil (:on-failure data))]]
    (cond [(= type "prompt")
           `(do
             (prompting-command :name ~name
                                :output ~output
                                :required-input ~required-input
                                :on-success ~on-success
                                :on-failure ~on-failure))]
          [(= type "output")
           `(do
             (output-command :name ~name
                             :output ~output
                             :args ~args
                             :on-success ~on-success
                             :on-failure ~on-failure))])))


(defmacro output-command [&rest forms]
  (define [[data (group-map keyword? forms)]
           [name (one `nil (:name data))]
           [output (one `nil (:output data))]
           [args (one `nil (:args data))]
           [required-input (one `nil (:required-input data))]
           [on-success (one `nil (:on-success data))]
           [on-failure (one `nil (:on-failure data))]]
    `((fn []
        (if-not (and (= (type ~on-success) list)
                     (even? (len ~on-success)))
                (raise (throw (MockSSH.MockSSHError
                               "on-success argument must be an even list of strings"))))
        (if-not (and (= (type ~on-failure) list)
                     (even? (len ~on-failure)))
                (raise (throw (MockSSH.MockSSHError
                               "on-failure argument must be an even list of strings"))))

        (setv success-callbacks [])
        (setv it (iter ~on-success))
        (for [callback (zip it it)]
          (setv on-success-action (get callback 0))
          (setv on-success-parameter (get callback 1))
          (when (= on-success-action "write")
            (do
             (.append success-callbacks 
                      (lambda (instance) 
                        (.writeln instance
                                  (bytes on-success-parameter)))))))

        (setv failure-callbacks [])
        (setv it (iter ~on-failure))
        (for [callback (zip it it)]
          (setv on-failure-action (get callback 0))
          (setv on-failure-parameter (get callback 1))
          (when (= on-success-action "write")
            (do
             (.append failure-callbacks 
                      (lambda (instance) 
                        (.writeln instance
                                  (bytes on-failure-parameter)))))))
      
        (MockSSH.ArgumentValidatingCommand ~name success-callbacks failure-callbacks ~@args)))))


(defmacro prompting-command [&rest forms]
  (define [[data (group-map keyword? forms)]
           [name (one `nil (:name data))]
           [output (one `nil (:output data))]
           [required-input (one `nil (:required-input data))]
           [on-success (one `nil (:on-success data))]
           [on-failure (one `nil (:on-failure data))]]
    `((fn []
        ;; on-success arg example: ["prompt" "hostname# "]
        (if-not (cond [(= (type ~on-success) list)
                       (= (len ~on-success) 2)])
                (raise (throw (MockSSH.MockSSHError
                               "on-success argument must be a list of two"))))

        (setv on-success-action (get ~on-success 0))
        (setv on-success-parameter (get ~on-success 1))
        
        ;; on-failure arg example: ["write" "Password is 1234!"]
        (if-not (cond [(= (type ~on-failure) list)
                       (= (len ~on-failure) 2)])
                (raise (throw (MockSSH.MockSSHError
                               "on-failure argument must be a list of at least two"))))

        (setv on-failure-action (get ~on-failure 0))
        (setv on-failure-parameter (get ~on-failure 1))
        
        ;; --- configure commands requirements ---
        (setv success-callbacks [])
        (setv failure-callbacks [])
        (when (= on-success-action "prompt")
          (do
           (.append success-callbacks
                    (lambda (instance) 
                      (setv instance.protocol.prompt
                            (bytes on-success-parameter))))))
           
        (when (= on-failure-action "write")
          (do
           (.append failure-callbacks 
                    (lambda (instance) 
                      (.writeln instance
                                (bytes on-failure-parameter))))))
      
        (apply MockSSH.PromptingCommand []
               {"name" ~name
                "password" (bytes ~required-input)
                "password_prompt" (bytes ~output)
                "success_callbacks" success-callbacks
                "failure_callbacks" failure-callbacks})))))
