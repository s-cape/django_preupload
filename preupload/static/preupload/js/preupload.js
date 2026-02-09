/**
 * Preupload client controller: preupload file on change, block submit while uploading.
 * No dependencies; attach to forms containing [data-preupload] widgets.
 */
(function () {
    "use strict";

    var STATES = { idle: "idle", uploading: "uploading", ready: "ready", error: "error" };

    function getFormConfig(form) {
        var w = form.querySelector("[data-preupload]");
        if (w) {
            var preuploadUrl = w.getAttribute("data-preupload-url");
            var csrfToken = w.getAttribute("data-preupload-csrf-token");
            if (preuploadUrl) return { preuploadUrl: preuploadUrl, csrfToken: csrfToken };
        }
        var preuploadUrl = form.getAttribute("data-preupload-url");
        var csrfToken = form.getAttribute("data-preupload-csrf-token");
        if (preuploadUrl && csrfToken !== null) return { preuploadUrl: preuploadUrl, csrfToken: csrfToken };
        var el = document.getElementById("preupload-config");
        if (el && el.textContent) {
            try {
                var c = JSON.parse(el.textContent);
                return { preuploadUrl: c.preuploadUrl || c.preupload_url, csrfToken: c.csrfToken || c.csrf_token };
            } catch (e) {}
        }
        return null;
    }

    function getCsrfFromCookie() {
        var name = "csrftoken";
        var cookies = document.cookie.split(";");
        for (var i = 0; i < cookies.length; i++) {
            var parts = cookies[i].trim().split("=");
            if (parts[0] === name) return parts[1] ? decodeURIComponent(parts[1].trim()) : "";
        }
        return "";
    }

    function PreuploadWidget(el, form) {
        this.el = el;
        this.form = form;
        this.fileInput = el.querySelector('input[type="file"]');
        this.tokenInput = el.querySelector('input[type="hidden"]');
        this.state = STATES.idle;
        if (!this.fileInput || !this.tokenInput) return;
        var self = this;
        this.fileInput.addEventListener("change", function () {
            self.onFileChange();
        });
    }

    PreuploadWidget.prototype.onFileChange = function () {
        var file = this.fileInput.files && this.fileInput.files[0];
        if (!file) {
            this.setState(STATES.idle);
            if (this.tokenInput) this.tokenInput.value = "";
            return;
        }
        this.upload(file);
    };

    PreuploadWidget.prototype.upload = function (file) {
        var config = getFormConfig(this.form);
        if (!config || !config.preuploadUrl) {
            this.setState(STATES.error);
            this.dispatch("preupload:error", { detail: { reason: "no-config" } });
            return;
        }
        var self = this;
        var xhr = new XMLHttpRequest();
        var formData = new FormData();
        formData.append("file", file);
        var csrf = (config.csrfToken !== undefined && config.csrfToken !== null && config.csrfToken !== "")
            ? config.csrfToken
            : getCsrfFromCookie();
        if (csrf) formData.append("csrfmiddlewaretoken", csrf);

        this.setState(STATES.uploading);
        this.dispatch("preupload:start", { detail: { file: file } });

        xhr.upload.addEventListener("progress", function (e) {
            if (e.lengthComputable) {
                self.dispatch("preupload:progress", { detail: { loaded: e.loaded, total: e.total } });
            }
        });
        xhr.addEventListener("load", function () {
            if (xhr.status >= 200 && xhr.status < 300) {
                try {
                    var data = JSON.parse(xhr.responseText);
                    if (data.token && self.tokenInput) {
                        self.tokenInput.value = data.token;
                    }
                    self.setState(STATES.ready);
                    self.dispatch("preupload:complete", { detail: data });
                } catch (err) {
                    self.setState(STATES.error);
                    self.dispatch("preupload:error", { detail: { reason: "parse", xhr: xhr } });
                }
            } else {
                self.setState(STATES.error);
                self.dispatch("preupload:error", { detail: { reason: "http", status: xhr.status, xhr: xhr } });
                if (self.tokenInput) self.tokenInput.value = "";
            }
        });
        xhr.addEventListener("error", function () {
            self.setState(STATES.error);
            self.dispatch("preupload:error", { detail: { reason: "network" } });
            if (self.tokenInput) self.tokenInput.value = "";
        });
        xhr.open("POST", config.preuploadUrl);
        xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");
        xhr.send(formData);
    };

    PreuploadWidget.prototype.setState = function (s) {
        this.state = s;
        this.el.setAttribute("data-preupload-state", s);
    };

    PreuploadWidget.prototype.dispatch = function (type, opts) {
        this.el.dispatchEvent(new CustomEvent(type, opts || { bubbles: true }));
    };

    function attachForm(form) {
        var config = getFormConfig(form);
        if (!config || !config.preuploadUrl) return [];
        var widgets = form.querySelectorAll("[data-preupload]");
        var list = [];
        for (var i = 0; i < widgets.length; i++) {
            list.push(new PreuploadWidget(widgets[i], form));
        }
        form.addEventListener("submit", function (e) {
            var uploading = false;
            for (var j = 0; j < list.length; j++) {
                if (list[j].state === STATES.uploading) {
                    uploading = true;
                    break;
                }
            }
            if (uploading) {
                e.preventDefault();
                var warn = typeof window.preuploadWarn === "function"
                    ? window.preuploadWarn
                    : function (ctx) {
                          window.alert("Please wait for the upload to finish.");
                      };
                warn({ form: form, widgets: list });
            }
        });
        return list;
    }

    function init() {
        var forms = document.querySelectorAll("form");
        for (var i = 0; i < forms.length; i++) {
            if (forms[i].querySelector("[data-preupload]")) {
                attachForm(forms[i]);
            }
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }

    window.Preupload = { attachForm: attachForm, STATES: STATES };
})();
