(function () {
  "use strict";

  var navToggle = document.querySelector("[data-nav-toggle]");
  var mainNav = document.querySelector("[data-main-nav]");
  if (navToggle && mainNav) {
    navToggle.addEventListener("click", function () {
      mainNav.classList.toggle("is-open");
    });
  }

  var root = document.documentElement;
  var THEME_INTERVAL_MS = 5 * 60 * 1000;

  function applyTheme(theme) {
    root.setAttribute("data-theme", theme);
    root.classList.add("theme-transition");
    window.setTimeout(function () {
      root.classList.remove("theme-transition");
    }, 500);
  }

  function toggleTheme() {
    applyTheme(root.getAttribute("data-theme") === "dark" ? "light" : "dark");
  }

  applyTheme("light");
  window.setInterval(toggleTheme, THEME_INTERVAL_MS);

  var carousel = document.querySelector("[data-hero-carousel]");
  if (!carousel) return;

  var slides = carousel.querySelectorAll(".hero-slide");
  var dots = carousel.querySelectorAll(".hero-dot");
  if (slides.length <= 1) return;

  var index = 0;
  var timer;

  function show(i) {
    index = (i + slides.length) % slides.length;
    slides.forEach(function (slide, idx) {
      slide.classList.toggle("is-active", idx === index);
    });
    dots.forEach(function (dot, idx) {
      dot.classList.toggle("is-active", idx === index);
    });
  }

  function next() {
    show(index + 1);
  }

  function start() {
    stop();
    timer = setInterval(next, 6000);
  }

  function stop() {
    if (timer) clearInterval(timer);
  }

  dots.forEach(function (dot, idx) {
    dot.addEventListener("click", function () {
      show(idx);
      start();
    });
  });

  carousel.addEventListener("mouseenter", stop);
  carousel.addEventListener("mouseleave", start);
  start();
})();
