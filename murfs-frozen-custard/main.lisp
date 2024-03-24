(defpackage :murfs
  (:use :common-lisp)
  (:export #:main))

(in-package :murfs)

(defparameter *murfs-url* "https://www.murfsfrozencustard.com/flavorForecast")

(defun remove-leading-whitespace (str)
  "Remove the leading whitespace from a string."
  (let ((position (position-if #'alphanumericp str)))
	(if (eq position nil)
		""
		(subseq str position))))


(defun get-children-of-class (element class &key tag-name)
  "Get all children matching the given class. This function is not recursive."
  (loop for child across (plump:children element)
		if (and
			(typep child 'plump-dom:element) ; Text nodes to not have a class
			(if (not tag-name) (equalp (plump:tag-name child) tag-name) t)
			(plump:has-attribute child "class")
			(equalp (plump:get-attribute child "class") class)) ; EQUALP is not case-sensitive
		  collect child))

(defun get-flavor-elements (parsed)
  "Get the flavor elements from the parsed DOM."
  (get-children-of-class
   (plump:get-element-by-id parsed "rightWeeklyFlavorList")
   "weeklyFlavorBlock"
   :tag-name "div"))

(defun get-flavor-details (flavor-div)
  "Get the details from the flavor DIV."
  (let ((date
		  (let* ((date-div (car (get-children-of-class flavor-div "weeklyFlavorDate" :tag-name "div")))
				 (day-of-week-span (car (get-children-of-class date-div "weeklyDateDay" :tag-name "span")))
				 (date-span (car (get-children-of-class date-div "weeklyDateNumber" :tag-name "span"))))
			(cons
			 (remove-leading-whitespace (get-text-from-element day-of-week-span))
			 (remove-leading-whitespace (get-text-from-element date-span)))))
		(image-url
		  (let* ((image-div (car (get-children-of-class flavor-div "weeklyFlavorImage" :tag-name "div")))
				 (img-element (car (plump:get-elements-by-tag-name image-div "img"))))
			(plump:get-attribute img-element "src")))
		(flavor
		  (let* ((flavor-details-div (car (get-children-of-class flavor-div "weeklyFlavorDetails" :tag-name "div")))
				 (flavor-name-div (car (get-children-of-class flavor-details-div "weeklyFlavorName" :tag-name "div")))
				 (flavor-name (remove-leading-whitespace (get-text-from-element (car (plump:get-elements-by-tag-name flavor-name-div "span")))))
				 (flavor-description-div (car (get-children-of-class flavor-details-div "weeklyFlavorDescription" :tag-name "div")))
				 (flavor-description (remove-leading-whitespace (get-text-from-element (car (plump:get-elements-by-tag-name flavor-description-div "span"))))))
			(cons flavor-name flavor-description))))
	(list date image-url flavor)))

(declaim (ftype (function (plump:element) string) get-text-from-element))
(defun get-text-from-element (element)
  "Get the text from an element. Plump leaves these as normal elements, with one child text element."
  (car (multiple-value-list (plump:text (plump:first-child element)))))

(declaim (ftype (function (string) list) download-flavors))
(defun download-flavors (url)
  "Download the flavors."
  (let* ((headers '(("User-Agenet" . "Mozilla/5.0 (Windows NT 10.0; rv:122.0) Gecko/20100101 Firefox/122.0")
					("DNT" . 1)
					("SEC-GPC" . 1)))
		 (dom (plump:parse (dex:get url :headers headers))))
	(loop for flavor in (get-flavor-elements dom)
		  collect (get-flavor-details flavor))))


;;; Build the ATOM feed

(declaim (ftype (function (list) hash-table) make-attribute-map))
(defun make-attribute-map (attributes)
  "Create an attribute map with the given attributes. ATTRIBUTES should be a list of conses."
  (let ((map (plump:make-attribute-map)))
	(loop for attribute in attributes
		  do (setf (gethash (car attribute) map) (cdr attribute)))
	map))

(declaim (ftype (function (string &key (:link-self string) (:link-other string)) (values plump:root plump:element)) make-feed-root))
(defun make-feed-root (title &key link-self link-other)
  "Make the root node of the ATOM feed."
  (let ((root (plump:make-root)))
	;; PLUMP:MAKE-XML-HEADER automatically adds the header to the parent (root in this case)
	(plump:make-xml-header root :attributes (make-attribute-map '(("version" . "1.0") ("encoding" . "utf-8"))))
	(let ((feed (plump:make-element root "feed" :attributes (make-attribute-map '(("xmlns" . "http://www.w3.org/2005/Atom"))))))
	  (plump:make-fulltext-element feed "title" :text title)
	  (plump:make-fulltext-element feed "id" :text "Murph-Custard")
	  (plump:make-fulltext-element feed "updated" :text (get-timestamp))
	  (when link-self
		(plump:make-fulltext-element feed "link" :attributes (make-attribute-map `(("href" . ,link-self) ("rel" . "self")))))
	  (when link-other
		(plump:make-fulltext-element feed "link" :attributes (make-attribute-map `(("href" . ,link-other)))))
	  (values root feed))))

(declaim (ftype (function (string) fixnum) short-day-name-to-int))
(defun short-day-name-to-int (name)
  "Convert the short name of a day to an int (e.g. \"Mon\" -> 1"
  (position name #("Sun" "Mon" "Tue" "Wed" "Thu" "Fri" "Sat") :test 'equalp))

(declaim (ftype (function (&optional t) string) get-timestamp))
(defun get-timestamp (&optional day)
  "Generate the timestamp. Day is the next weekday in shortened form."
  (if (eq nil day)
	  (local-time:to-rfc3339-timestring (local-time:today))
	  (let ((day-of-week (local-time:timestamp-day-of-week (local-time:today))))
		(local-time:to-rfc3339-timestring
		 ;; (car (multiple-value-list)) limits the return to only one value
		 (car (multiple-value-list (local-time:timestamp+ (local-time:today) (abs (- day-of-week (short-day-name-to-int day))) :day)))))))

(declaim (ftype (function (list) string) make-id))
(defun make-id (item)
  "Make an id."
  (get-timestamp (caar item)))

(declaim (ftype (function (list plump-dom:element) *) add-item-to-feed))
(defun add-item-to-feed (item feed-root)
  "Add ITEM to the XML.
Item has the format (((DayOfWeek . Date) Image-URL (Title . Description)))"
  (let ((entry (plump:make-element feed-root "entry")))
	(plump:make-fulltext-element entry "title" :text (car (nth 2 item)))
	(plump:make-fulltext-element entry "author" :text "Automation")
	(plump:make-fulltext-element entry "id" :text (make-id item))
	(plump:make-fulltext-element entry "updated" :text (get-timestamp (caar item)))
	(plump:make-fulltext-element entry "summary" :text (cdr (nth 2 item)))))
	

(declaim (ftype (function (list plump-dom:element) *) add-items-to-feed))
(defun add-items-to-feed (items feed-root)
  "Add items to the feed."
  (dolist (flavor items)
	(declare (type list flavor))
	(add-item-to-feed flavor feed-root)))

(defun main()
  "The main function."
  (let ((results (download-flavors *murfs-url*)))
	(multiple-value-bind (root feed) (make-feed-root "Murph's Custard" :link-other *murfs-url*)
	  (add-items-to-feed results feed)
	  ;; TODO: Write to file here
	  (plump:serialize root))))
