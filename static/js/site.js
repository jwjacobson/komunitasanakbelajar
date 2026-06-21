/* Komunitas Anak Belajar — front-end behaviors (DESIGN §7). Vanilla JS, no deps.
   Loaded with `defer`, so the DOM is parsed before this runs. */
(function () {
    "use strict";

    /* ----------------------------------------------------------------------
       Hero slideshow: crossfade, auto-advance 4s, pause on hover, manual
       dots + prev/next arrows, honors prefers-reduced-motion (no autoplay).
       ---------------------------------------------------------------------- */
    function initSlideshow(root) {
        var slides = Array.prototype.slice.call(
            root.querySelectorAll("[data-slide]")
        );
        if (slides.length === 0) {
            return;
        }

        var dotsWrap = root.querySelector("[data-slide-dots]");
        var prevBtn = root.querySelector("[data-slide-prev]");
        var nextBtn = root.querySelector("[data-slide-next]");
        var reduceMotion =
            window.matchMedia &&
            window.matchMedia("(prefers-reduced-motion: reduce)").matches;

        var index = 0;
        var timer = null;

        // Build one dot per slide.
        var dots = [];
        if (dotsWrap) {
            slides.forEach(function (_, n) {
                var dot = document.createElement("button");
                dot.type = "button";
                dot.className = "slideshow__dot" + (n === 0 ? " is-active" : "");
                dot.setAttribute("aria-label", "Foto " + (n + 1));
                dot.addEventListener("click", function () {
                    go(n);
                    restart();
                });
                dotsWrap.appendChild(dot);
                dots.push(dot);
            });
        }

        function go(n) {
            slides[index].classList.remove("is-active");
            slides[index].setAttribute("aria-hidden", "true");
            if (dots[index]) {
                dots[index].classList.remove("is-active");
            }
            index = (n + slides.length) % slides.length;
            slides[index].classList.add("is-active");
            slides[index].setAttribute("aria-hidden", "false");
            if (dots[index]) {
                dots[index].classList.add("is-active");
            }
        }

        function start() {
            if (reduceMotion || slides.length < 2) {
                return;
            }
            stop();
            timer = window.setInterval(function () {
                go(index + 1);
            }, 4000);
        }

        function stop() {
            if (timer) {
                window.clearInterval(timer);
                timer = null;
            }
        }

        function restart() {
            stop();
            start();
        }

        if (nextBtn) {
            nextBtn.addEventListener("click", function () {
                go(index + 1);
                restart();
            });
        }
        if (prevBtn) {
            prevBtn.addEventListener("click", function () {
                go(index - 1);
                restart();
            });
        }

        // Pause on hover.
        root.addEventListener("mouseenter", stop);
        root.addEventListener("mouseleave", start);

        start();
    }

    /* ----------------------------------------------------------------------
       ID/EN language toggle: a general "show the active language" switch.
       Any element tagged [data-lang-pane="id"|"en"] (rendered both ways
       server-side) is shown or hidden to match the active language. This drives
       the Tentang/Dukung bodies, the homepage hero (title, subtitle, buttons),
       and the nav "Dukung kami" CTA. Default ID; the choice persists in
       localStorage across pages. Nav links and donation-card labels are left
       untagged, so they stay put.
       ---------------------------------------------------------------------- */
    var STORAGE_KEY = "kab-lang";

    function storedLang() {
        try {
            var value = window.localStorage.getItem(STORAGE_KEY);
            return value === "en" ? "en" : "id"; // default ID
        } catch (e) {
            return "id";
        }
    }

    function persistLang(lang) {
        try {
            window.localStorage.setItem(STORAGE_KEY, lang);
        } catch (e) {
            /* storage unavailable (e.g. private mode) — toggle still works for
               the current page, it just won't persist. */
        }
    }

    function applyLang(lang) {
        // Content panes.
        var panes = document.querySelectorAll("[data-lang-pane]");
        Array.prototype.forEach.call(panes, function (pane) {
            pane.hidden = pane.getAttribute("data-lang-pane") !== lang;
        });
        // Toggle buttons (reflect the active language).
        var buttons = document.querySelectorAll("[data-lang-toggle] [data-lang]");
        Array.prototype.forEach.call(buttons, function (btn) {
            var on = btn.getAttribute("data-lang") === lang;
            btn.classList.toggle("is-active", on);
            btn.setAttribute("aria-pressed", on ? "true" : "false");
        });
    }

    function initLangToggle() {
        var current = storedLang();
        applyLang(current);

        var buttons = document.querySelectorAll("[data-lang-toggle] [data-lang]");
        Array.prototype.forEach.call(buttons, function (btn) {
            btn.addEventListener("click", function () {
                var lang = btn.getAttribute("data-lang") === "en" ? "en" : "id";
                persistLang(lang);
                applyLang(lang);
            });
        });
    }

    /* ---------------------------------------------------------------------- */
    var slideshows = document.querySelectorAll("[data-slideshow]");
    Array.prototype.forEach.call(slideshows, initSlideshow);
    initLangToggle();
})();
