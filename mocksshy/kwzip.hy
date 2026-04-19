(import collections [defaultdict])
(import functools [reduce])
(import hy.models [Keyword])


(defn keyword? [k]
  (isinstance k Keyword))


(defn one [default args]
  (cond
    (= (len args) 0) default
    (= (len args) 1) (get args 0)
    True (raise (TypeError "Too many args passed in."))))


(defn key-value-stream [key? stream]
  (let [key None]
    (for [x stream]
      (if (key? x)
        (setv key x)
        (yield [key x])))))


(defn group-map [key? stream]
  (reduce
    (fn [accum v]
      (let [[key value] v]
        (.append (get accum key) value))
      accum)
    (key-value-stream key? stream)
    (defaultdict list)))
