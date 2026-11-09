const menuButton = document.querySelector(".menu-toggle");
const navigation = document.querySelector(".primary-nav");

if (menuButton && navigation) {
  const mobileNavigation = window.matchMedia("(max-width: 860px)");

  const setMenuOpen = (isOpen) => {
    menuButton.setAttribute("aria-expanded", String(isOpen));
    menuButton.setAttribute(
      "aria-label",
      isOpen ? menuButton.dataset.closeLabel : menuButton.dataset.openLabel,
    );
    navigation.classList.toggle("is-open", isOpen);
  };

  menuButton.addEventListener("click", () => {
    const isOpen = menuButton.getAttribute("aria-expanded") === "true";
    setMenuOpen(!isOpen);
  });

  navigation.addEventListener("click", (event) => {
    if (event.target.closest("a") && mobileNavigation.matches) {
      setMenuOpen(false);
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && menuButton.getAttribute("aria-expanded") === "true") {
      setMenuOpen(false);
      menuButton.focus();
    }
  });

  document.addEventListener("click", (event) => {
    if (
      mobileNavigation.matches &&
      menuButton.getAttribute("aria-expanded") === "true" &&
      !event.target.closest(".site-header")
    ) {
      setMenuOpen(false);
    }
  });

  mobileNavigation.addEventListener("change", () => setMenuOpen(false));
}

const carousel = document.querySelector("[data-carousel]");

if (carousel) {
  const track = carousel.querySelector("[data-carousel-track]");
  const slides = Array.from(carousel.querySelectorAll("[data-carousel-slide]"));
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const pauseRegion = carousel.closest(".hero") || carousel;

  if (track && slides.length > 1) {
    let activeIndex = 0;
    let timerId = null;
    let userPaused = reducedMotion.matches;
    let pointerPaused = false;

    const stopAutoplay = () => {
      if (timerId !== null) {
        window.clearInterval(timerId);
        timerId = null;
      }
    };

    const syncAutoplay = () => {
      const shouldRun =
        !userPaused &&
        !pointerPaused &&
        !document.hidden;

      if (shouldRun && timerId === null) {
        timerId = window.setInterval(showNext, 2000);
      } else if (!shouldRun) {
        stopAutoplay();
      }
    };

    const showSlide = (index) => {
      activeIndex = (index + slides.length) % slides.length;
      track.style.transform = `translate3d(-${activeIndex * 100}%, 0, 0)`;

      slides.forEach((slide, slideIndex) => {
        const isActive = slideIndex === activeIndex;
        slide.setAttribute("aria-hidden", String(!isActive));
        slide.inert = !isActive;
      });

    };

    function showNext() {
      showSlide(activeIndex + 1);
    }

    pauseRegion.addEventListener("pointerenter", (event) => {
      if (event.pointerType === "mouse") {
        pointerPaused = true;
        syncAutoplay();
      }
    });

    pauseRegion.addEventListener("pointerleave", (event) => {
      if (event.pointerType === "mouse") {
        pointerPaused = false;
        syncAutoplay();
      }
    });

    document.addEventListener("visibilitychange", syncAutoplay);
    reducedMotion.addEventListener("change", (event) => {
      userPaused = event.matches;
      syncAutoplay();
    });

    syncAutoplay();
  }
}
