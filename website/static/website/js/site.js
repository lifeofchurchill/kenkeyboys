/*
  Kenkey Boys FC: site behaviour.
  Everything in this file is an extra on top of a page that already works.
  If it fails to load, visitors still see every section and every number.
*/

// Respect visitors who have asked their device for less motion
const prefersLessMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;


/* ---------- Phone menu ---------- */
function setUpMobileMenu() {
  const header = document.querySelector(".site-header");
  const toggle = document.querySelector(".menu-toggle");
  const nav = document.getElementById("site-nav");
  if (!header || !toggle || !nav) return;

  const label = toggle.querySelector(".menu-toggle__text");

  // Open or close the menu, keeping the button's label and aria-expanded in step
  function setOpen(open) {
    nav.classList.toggle("is-open", open);
    toggle.setAttribute("aria-expanded", String(open));
    label.textContent = open ? "Close" : "Menu";
  }

  // Each tap flips it: open if closed, closed if open
  toggle.addEventListener("click", () => setOpen(!nav.classList.contains("is-open")));

  // The Escape key closes it and puts keyboard focus back on the button
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && nav.classList.contains("is-open")) {
      setOpen(false);
      toggle.focus();
    }
  });

  // If the window is widened past phone size, the full menu shows anyway,
  // so reset the button to "closed" for next time the window gets narrow
  window.matchMedia("(min-width: 1025px)").addEventListener("change", (event) => {
    if (event.matches) setOpen(false);
  });

  // Only now, with the button working, let the CSS fold the menu away on small screens
  header.classList.add("menu-ready");
}


/* ---------- Live countdown to the next match ---------- */
function startCountdown() {
  const clock = document.querySelector(".countdown[data-kickoff]");
  if (!clock) return; // no upcoming match on this page

  // data-kickoff="..." in the HTML is read here as clock.dataset.kickoff
  const kickoff = new Date(clock.dataset.kickoff).getTime();
  // The four number boxes, in order: days, hours, minutes, seconds
  const boxes = clock.querySelectorAll(".countdown__value");
  let timer = null;

  function tick() {
    // The same maths as countdown_parts() in views.py, now running every second
    const remaining = Math.max(0, Math.floor((kickoff - Date.now()) / 1000));
    let seconds = remaining;
    const days = Math.floor(seconds / 86400);
    seconds %= 86400;
    const hours = Math.floor(seconds / 3600);
    seconds %= 3600;
    const minutes = Math.floor(seconds / 60);
    seconds %= 60;

    [days, hours, minutes, seconds].forEach((value, i) => {
      boxes[i].textContent = String(value).padStart(2, "0");
    });

    // Stop the clock once kick-off arrives
    if (remaining === 0 && timer) clearInterval(timer);
  }

  tick();
  timer = setInterval(tick, 1000);
}


/* ---------- Rotating news stories ---------- */
function setUpNewsCarousel() {
  const carousel = document.querySelector(".carousel");
  if (!carousel) return;

  const track = carousel.querySelector(".carousel__track");
  const slides = track.querySelectorAll(".news-slide");
  if (slides.length < 2) return; // one story has nothing to rotate to

  const bar = carousel.querySelector(".carousel__bar");
  const dots = carousel.querySelectorAll(".carousel__dot");
  const progress = carousel.querySelector(".carousel__progress");
  const fill = progress.querySelector("span");
  const pauseButton = carousel.querySelector("[data-carousel='pause']");

  let current = 0;      // which story is showing: 0 is the first
  let paused = false;   // set by the pause button
  let holding = false;  // true while the mouse, or keyboard focus, is on the carousel

  // Show a story by its position
  function show(index) {
    // Wrap around, so "next" after the last story goes back to the first
    current = (index + slides.length) % slides.length;
    // Every story is exactly one track-width wide, so story 3 starts at 3 widths in
    track.scrollTo({ left: current * track.clientWidth });
    dots.forEach((dot, i) => dot.setAttribute("aria-current", String(i === current)));
    restartTimer();
  }

  // The gold line IS the timer: when its fill animation ends, the next story shows.
  // Pausing the animation therefore pauses the rotation too
  function restartTimer() {
    fill.classList.remove("is-running");
    void fill.offsetWidth; // makes the browser notice the removal, so the fill starts again from empty
    fill.classList.add("is-running");
    updateTimer();
  }

  function updateTimer() {
    fill.style.animationPlayState = paused || holding ? "paused" : "running";
  }

  fill.addEventListener("animationend", () => show(current + 1));

  // Arrows and dots
  carousel.querySelector("[data-carousel='prev']").addEventListener("click", () => show(current - 1));
  carousel.querySelector("[data-carousel='next']").addEventListener("click", () => show(current + 1));
  dots.forEach((dot, i) => dot.addEventListener("click", () => show(i)));

  // Pause button: flips between paused and playing
  pauseButton.addEventListener("click", () => {
    paused = !paused;
    pauseButton.setAttribute("aria-pressed", String(paused));
    updateTimer();
  });

  // Hold still while someone is reading with the mouse over it...
  carousel.addEventListener("mouseenter", () => { holding = true; updateTimer(); });
  carousel.addEventListener("mouseleave", () => { holding = false; updateTimer(); });
  // ...or moving through it with the keyboard. :focus-visible is only true for keyboard
  // focus, so clicking an arrow with the mouse doesn't freeze the rotation afterwards
  carousel.addEventListener("focusin", (event) => {
    if (event.target.matches(":focus-visible")) { holding = true; updateTimer(); }
  });
  carousel.addEventListener("focusout", () => { holding = false; updateTimer(); });

  // If someone swipes or scrolls the stories by hand, keep the dots in step.
  // Wait until the scrolling has settled for 150ms before working out where it stopped
  let scrollPause = null;
  track.addEventListener("scroll", () => {
    clearTimeout(scrollPause);
    scrollPause = setTimeout(() => {
      const index = Math.round(track.scrollLeft / track.clientWidth);
      if (index !== current) show(index);
    }, 150);
  });

  // Visitors who asked for less motion get no automatic rotation:
  // the timer and pause button are hidden, the arrows and dots still work
  if (prefersLessMotion) {
    progress.hidden = true;
    pauseButton.hidden = true;
  }

  // Switch on the controls and start
  carousel.classList.add("carousel--live");
  bar.hidden = false;
  show(0);
}


/* ---------- Squad position filter (used on the squad page) ---------- */
function setUpSquadFilter() {
  const filter = document.querySelector(".squad-filter");
  if (!filter) return;

  const buttons = filter.querySelectorAll("button");
  const cards = document.querySelectorAll(".player-card[data-group]");

  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      const group = button.dataset.filter; // "ALL", "ATT", "MID", "DEF" or "GK"
      buttons.forEach((b) => b.setAttribute("aria-pressed", String(b === button)));
      cards.forEach((card) => {
        card.hidden = group !== "ALL" && card.dataset.group !== group;
      });
    });
  });

  // The buttons start hidden in the HTML; show them now that they can work
  filter.hidden = false;
}


/* ---------- Sections rising into view as you scroll ---------- */
function setUpReveals() {
  if (!("IntersectionObserver" in window)) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target); // animate each one only once
      }
    });
  }, { threshold: 0.12 });

  document.querySelectorAll(".reveal").forEach((item) => {
    if (item.getBoundingClientRect().top < window.innerHeight) {
      // Already on screen when the page opens: show it straight away, so nothing flickers
      item.classList.add("is-visible");
    } else {
      observer.observe(item);
    }
  });

  document.documentElement.classList.add("reveals-on");
}


/* ---------- Crest tilting towards the mouse ---------- */
function setUpCrestTilt() {
  const hero = document.querySelector(".hero");
  const crest = document.querySelector(".hero__crest img");
  if (!hero || !crest) return;

  hero.addEventListener("mousemove", (event) => {
    const box = hero.getBoundingClientRect();
    const x = (event.clientX - box.left) / box.width - 0.5;
    const y = (event.clientY - box.top) / box.height - 0.5;
    crest.style.transform = `perspective(900px) rotateY(${x * 14}deg) rotateX(${-y * 10}deg)`;
  });

  hero.addEventListener("mouseleave", () => {
    crest.style.transform = "";
  });
}


/* ---------- Start everything ---------- */
setUpMobileMenu();
startCountdown();
setUpNewsCarousel();
setUpSquadFilter();
if (!prefersLessMotion) {
  setUpReveals();
  setUpCrestTilt();
}