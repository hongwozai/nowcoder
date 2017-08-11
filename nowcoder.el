;;; 用于记录tpid, buffer-local变量
(defvar nowcoder-problem-tpid "0")
(defvar nowcoder-fail-buffer-name "*nowcoder-test-fail*")
(defvar nowcoder-python-program-path "/opt/nowcoder/")
(defvar nowcoder-python-program "nowcoder.py")
(defvar nowcoder-lang "python")

;;; 传代码拉结果
(defun nowcoder-push-and-pull ()
  (interactive)
  (if (not (local-variable-p 'nowcoder-problem-tpid))
      (message "tpId Fetch Error!")
      (let ((tempfile (make-temp-file "nowcoder")))
        (write-region (point-min) (point-max) tempfile)
        (let ((failbuf (get-buffer-create nowcoder-fail-buffer-name)))
          (with-current-buffer nowcoder-fail-buffer-name
            (let ((inhibit-read-only t)) (erase-buffer)))
          (async-shell-command
           (format "%s -pi %s -p %s -l %s"
                   nowcoder-python-program
                   nowcoder-problem-tpid
                   tempfile
                   nowcoder-lang)
           failbuf)
          (pop-to-buffer nowcoder-fail-buffer-name)
          )))
  )

;;; 独立的拉取结果函数
(defun nowcoder-test (tpId)
  (let ((tempfile (make-temp-file "nowcoder")))
    (write-region (point-min) (point-max) tempfile)
    (let ((failbuf (get-buffer-create nowcoder-fail-buffer-name)))
      (with-current-buffer nowcoder-fail-buffer-name
        (let ((inhibit-read-only t)) (erase-buffer)))
      (async-shell-command
       (format "%s -pi %s -p %s -l %s"
               nowcoder-python-program
               tpId
               tempfile
               nowcoder-lang)
       failbuf)
      (pop-to-buffer nowcoder-fail-buffer-name)
      ))
  )

;;; 拉题目
(defun nowcoder-fetch-problem (name order)
  (let ((buf (get-buffer-create (format "%s-%d" name order))))
    (with-current-buffer buf
      (make-variable-buffer-local 'nowcoder-problem-tpid)
      (erase-buffer)
      (cond ((string= "c" nowcoder-lang) (c++-mode))
            ((string= "python" nowcoder-lang) (python-mode))
            ((string= "java" nowcoder-lang) (java-mode)))
      (call-process-shell-command
       (format "%s -g %d -i %s -l %s"
               nowcoder-python-program
               order
               (concat nowcoder-python-program-path name)
               nowcoder-lang)
       nil buf)
      ;; tpid获取
      (goto-char (point-min))
      (re-search-forward "\\[-\\]tpId: \\(.*\\)")
      (setq-local nowcoder-problem-tpid (match-string-no-properties 1))
      (message (format "tpid: %s" nowcoder-problem-tpid))
      ;; 开始处理题目，将其改为注释
      (goto-char (point-min))
      (while (not (string-match-p "^======="
                                  (buffer-substring-no-properties
                                   (line-beginning-position)
                                   (line-end-position))))
        (beginning-of-line)
        (cond ((or (string= "c" nowcoder-lang)
                   (string= "java" nowcoder-lang)) (insert "// "))
              ((string= "python" nowcoder-lang) (insert "# ")))
        (forward-line))
      (beginning-of-line)
      (cond ((or (string= "c" nowcoder-lang)
                 (string= "java" nowcoder-lang)) (insert "// "))
            ((string= "python" nowcoder-lang) (insert "# ")))
      ;; 添加头文件与命名空间
      (cond ((string= nowcoder-lang "c")
             (progn (forward-line)
                    (insert "#include <iostream>\n")
                    (insert "#include <vector>\n")
                    (insert "using namespace std;\n\n")))
            ((string= nowcoder-lang "python")
             (goto-char (point-min))
             (insert "# -*- coding:utf-8 -*- \n")))
      (whitespace-cleanup)
      ;; 添加快捷键
      (evil-local-set-key 'normal
                          (kbd "\C-c\C-c") 'nowcoder-push-and-pull)
      )
    (pop-to-buffer buf))
  )

(defun nowcoder-coding-interviews (order)
  (interactive "nCoding-Interviews N: ")
  (nowcoder-fetch-problem "coding-interviews" order))

(provide 'nowcoder)