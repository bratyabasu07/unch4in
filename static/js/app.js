/* ═══════════════════════════════════════════════════════════════
   MEDIUMPREMIUM — FUTURISTIC HACKER UI
   Author: Elliot Jr aka bratyabasu07
   ═══════════════════════════════════════════════════════════════ */

// ── Matrix Rain Effect ───────────────────────────────────────────
class MatrixRain {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.chars = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン0123456789ABCDEF<>/{}[]";
    this.fontSize = 14;
    this.columns = 0;
    this.drops = [];
    this.animId = null;
    this.init();
  }

  init() {
    this.resize();
    window.addEventListener("resize", () => this.resize());
    this.animate();
  }

  resize() {
    this.canvas.width = window.innerWidth;
    this.canvas.height = window.innerHeight;
    this.columns = Math.floor(this.canvas.width / this.fontSize);
    this.drops = Array(this.columns).fill(1).map(() => Math.random() * -50);
  }

  animate() {
    this.ctx.fillStyle = "rgba(10, 10, 15, 0.05)";
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    this.ctx.fillStyle = "#00ff41";
    this.ctx.font = `${this.fontSize}px monospace`;

    for (let i = 0; i < this.drops.length; i++) {
      const char = this.chars[Math.floor(Math.random() * this.chars.length)];
      const x = i * this.fontSize;
      const y = this.drops[i] * this.fontSize;
      this.ctx.globalAlpha = Math.random() * 0.5 + 0.1;
      this.ctx.fillText(char, x, y);
      this.drops[i]++;
      if (this.drops[i] * this.fontSize > this.canvas.height && Math.random() > 0.975) {
        this.drops[i] = 0;
      }
    }
    this.ctx.globalAlpha = 1;
    this.animId = requestAnimationFrame(() => this.animate());
  }
}

// ── Typing Effect ─────────────────────────────────────────────────
class TypeWriter {
  constructor(element, text, speed = 60) {
    this.element = element;
    this.text = text;
    this.speed = speed;
    this.index = 0;
  }

  start() {
    this.element.textContent = "";
    this.type();
  }

  type() {
    if (this.index < this.text.length) {
      this.element.textContent += this.text.charAt(this.index);
      this.index++;
      setTimeout(() => this.type(), this.speed + Math.random() * 40);
    }
  }
}

// ── Particle Effect on Click ──────────────────────────────────────
function createParticles(x, y) {
  const count = 8;
  for (let i = 0; i < count; i++) {
    const particle = document.createElement("div");
    const angle = (Math.PI * 2 * i) / count;
    const velocity = 40 + Math.random() * 40;
    particle.style.cssText = `
      position: fixed; left: ${x}px; top: ${y}px;
      width: 3px; height: 3px; border-radius: 50%;
      background: var(--neon-green);
      box-shadow: 0 0 6px var(--neon-green);
      pointer-events: none; z-index: 9999;
      transition: all 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94);
    `;
    document.body.appendChild(particle);
    requestAnimationFrame(() => {
      particle.style.transform = `translate(${Math.cos(angle) * velocity}px, ${Math.sin(angle) * velocity}px)`;
      particle.style.opacity = "0";
    });
    setTimeout(() => particle.remove(), 600);
  }
}

// ── Main App Controller ───────────────────────────────────────────
class App {
  constructor() {
    this.form = document.getElementById("url-form");
    this.input = document.getElementById("url-input");
    this.submitBtn = document.getElementById("submit-btn");
    this.errorEl = document.getElementById("error-msg");
    this.loadingOverlay = document.getElementById("loading-overlay");
    this.init();
  }

  init() {
    // Matrix rain
    const canvas = document.getElementById("matrix-rain");
    if (canvas) new MatrixRain(canvas);

    // Form handler
    if (this.form) {
      this.form.addEventListener("submit", (e) => this.handleSubmit(e));
    }

    // Click particles
    document.addEventListener("click", (e) => {
      if (e.target.closest("button") || e.target.closest("a")) {
        createParticles(e.clientX, e.clientY);
      }
    });

    // Terminal typing effect
    const terminalCmd = document.querySelector(".terminal-cmd-typing");
    if (terminalCmd) {
      new TypeWriter(terminalCmd, "python -m mediumpremium --serve --port 8000", 50).start();
    }

    // Auto-focus input
    if (this.input) {
      setTimeout(() => this.input.focus(), 800);
    }

    // Paste handler — auto submit on paste
    if (this.input) {
      this.input.addEventListener("paste", () => {
        setTimeout(() => {
          if (this.isValidUrl(this.input.value)) {
            this.form.dispatchEvent(new Event("submit"));
          }
        }, 100);
      });
    }

    // Intersection observer for fade-in
    this.observeElements();
  }

  async handleSubmit(e) {
    e.preventDefault();
    const url = this.input.value.trim();

    if (!url) {
      this.showError("No URL detected. Paste a Medium article link.");
      return;
    }

    if (!this.isValidUrl(url)) {
      this.showError("Invalid URL format. Enter a valid Medium article URL.");
      return;
    }

    if (!this.isMediumUrl(url)) {
      this.showError("This doesn't appear to be a Medium article URL.");
      return;
    }

    this.hideError();
    this.showLoading();

    try {
      // Navigate to the read page
      window.location.href = `/read?url=${encodeURIComponent(url)}`;
    } catch (err) {
      this.hideLoading();
      this.showError("Connection failed. Try again.");
    }
  }

  isValidUrl(str) {
    try {
      new URL(str);
      return true;
    } catch {
      return false;
    }
  }

  isMediumUrl(url) {
    const domains = [
      "medium.com", "towardsdatascience.com", "hackernoon.com",
      "betterprogramming.pub", "levelup.gitconnected.com",
      "blog.devgenius.io", "itnext.io", "codeburst.io",
      "uxplanet.org", "osintteam.blog", "infosecwriteups.com",
      "generativeai.pub", "productcoalition.com", "towardsdev.com",
      "bettermarketing.pub", "eand.co", "betterhumans.pub",
      "uxdesign.cc", "thebolditalic.com", "arcdigital.media",
      "psiloveyou.xyz", "writingcooperative.com",
      "entrepreneurshandbook.co", "prototypr.io", "theascent.pub",
      "storiusmag.com", "artificialcorner.com", "devopsquare.com",
      "javascript.plainenglish.io", "python.plainenglish.io",
      "ai.plainenglish.io", "blog.stackademic.com",
      "ai.gopubby.com", "blog.devops.dev", "code.likeagirl.io",
      "medium.datadriveninvestor.com", "blog.llamaindex.ai",
      "bashoverflow.com"
    ];
    try {
      const hostname = new URL(url).hostname.replace(/^www\./, "");
      // Known domain match
      if (domains.some(d => hostname === d || hostname.endsWith("." + d))) return true;
      // Custom domain: check if URL slug has a hex post ID pattern (8-12 hex chars after last dash)
      const slug = new URL(url).pathname.split("/").pop() || "";
      const hexMatch = slug.match(/-([a-f0-9]{8,12})$/i);
      return !!hexMatch;
    } catch {
      return false;
    }
  }

  showError(msg) {
    if (this.errorEl) {
      this.errorEl.textContent = msg;
      this.errorEl.classList.add("visible");
    }
  }

  hideError() {
    if (this.errorEl) this.errorEl.classList.remove("visible");
  }

  showLoading() {
    if (this.loadingOverlay) this.loadingOverlay.classList.add("active");
    if (this.submitBtn) this.submitBtn.classList.add("loading");
  }

  hideLoading() {
    if (this.loadingOverlay) this.loadingOverlay.classList.remove("active");
    if (this.submitBtn) this.submitBtn.classList.remove("loading");
  }

  observeElements() {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.style.opacity = "1";
          entry.target.style.transform = "translateY(0)";
        }
      });
    }, { threshold: 0.1 });

    document.querySelectorAll(".observe-fade").forEach(el => {
      el.style.opacity = "0";
      el.style.transform = "translateY(20px)";
      el.style.transition = "0.6s cubic-bezier(0.4, 0, 0.2, 1)";
      observer.observe(el);
    });
  }
}

// ── Boot ──────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  window.app = new App();
});
