(import [collections [defaultdict]]
        [functools [reduce]])


(defn keyword? [k] (and (instance? (type :foo) k)
                   (.startswith k (get :foo 0))))


(defn one [default args]
  (cond
    [(= (len args) 0) default]
    [(= (len args) 1) (get args 0)]
    [true (raise (TypeError "Too many args passed in."))]))


(defn key-value-stream [key? stream]
  (let [[key nil]]
    (for [x stream]
      (if (key? x)
        (setv key x)
        (yield [key x])))))


(defn group-map [key? stream]
  (reduce
    (fn [accum v]
      (let [[(, key value) v]]
        (.append (get accum key) value))
      accum)
    (key-value-stream key? stream)
    (defaultdict list)))
