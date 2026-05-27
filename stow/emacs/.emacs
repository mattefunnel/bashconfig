(require 'package) ;; You might already have this line
(when (< emacs-major-version 24)
  ;; For important compatibility libraries like cl-lib
  (add-to-list 'package-archives '("gnu" . "http://elpa.gnu.org/packages/")))
(add-to-list 'package-archives
             '("melpa-stable" . "https://stable.melpa.org/packages/") t)
;; Set your lisp system and, optionally, some contribs
(setq inferior-lisp-program "/usr/local/bin/sbcl")
(setq slime-contribs '(slime-fancy))

;; Added by Package.el.  This must come before configurations of
;; installed packages.  Don't delete this line.  If you don't want it,
;; just comment it out by adding a semicolon to the start of the line.
;; You may delete these explanatory comments.
(package-initialize)

(custom-set-variables
 ;; custom-set-variables was added by Custom.
 ;; If you edit it by hand, you could mess it up, so be careful.
 ;; Your init file should contain only one such instance.
 ;; If there is more than one, they won't work right.
 '(gud-gdb-command-name "gdb --annotate=1")
 '(indent-tabs-mode nil)
 '(large-file-warning-threshold nil)
 '(package-selected-packages (quote (slime))))
(custom-set-faces
 ;; custom-set-faces was added by Custom.
 ;; If you edit it by hand, you could mess it up, so be careful.
 ;; Your init file should contain only one such instance.
 ;; If there is more than one, they won't work right.
 '(font-lock-function-name-face ((((class color) (min-colors 88) (background light)) (:foreground "blue")))))

;; Manual set faces
(set-face-foreground 'minibuffer-prompt "green")

;; Backup settings
(setq
   backup-by-copying t      ; don't clobber symlinks
   backup-directory-alist
    '(("." . "~/.saves"))    ; don't litter my fs tree
   delete-old-versions t
   kept-new-versions 6
   kept-old-versions 2
   version-control t)       ; use versioned backups

;; js2-mode
;;(setq js-indent-level 2)
;;(add-to-list 'load-path "~/elisp")
;;(require 'js2-mode)

;; Misc. options
(setq column-number-mode t)
(setq vc-follow-symlinks t)


;; slime helper!
(setq inferior-lisp-program "sbcl")
;;(load (expand-file-name "~/quicklisp/slime-helper.el"))

;; Buffers and Windows
(defun transpose-windows ()
  "Transpose two windows.  If more or less than two windows are visible, error."
  (interactive)
  (unless (= 2 (count-windows))
    (error "There are not 2 windows."))
  (let* ((windows (window-list))
         (w1 (car windows))
         (w2 (nth 1 windows))
         (w1b (window-buffer w1))
         (w2b (window-buffer w2)))
    (set-window-buffer w1 w2b)
         (set-window-buffer w2 w1b)))


;; Keybindings
(global-set-key (kbd "C-x t") 'transpose-windows)

;; Misc
(server-start)

;; yank-pop-forwards
(defun yank-pop-forwards (arg)
      (interactive "p")
      (yank-pop (- arg)))
(global-set-key "\M-Y" 'yank-pop-forwards)

(defun copy-file-name-to-clipboard ()
  "Copy the current buffer file name to the clipboard."
  (interactive)
  (let ((filename (if (equal major-mode 'dired-mode)
                      default-directory
                    (buffer-file-name))))
    (when filename
      (kill-new filename)
      (message "Copied buffer file name '%s' to the clipboard." filename))))

;; gnu-apl-mode
;;(add-to-list 'load-path "~/code/gnu-apl-mode")
;;(require 'gnu-apl-mode)
