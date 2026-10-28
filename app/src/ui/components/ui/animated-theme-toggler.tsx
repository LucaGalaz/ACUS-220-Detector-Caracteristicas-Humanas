"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { flushSync } from "react-dom";
import { Moon, Sun } from "lucide-react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { cn } from "@/lib/utils";
import "./animated-theme-toggler.css";

type AnimatedThemeTogglerProps = { className?: string };

export function AnimatedThemeToggler({ className }: AnimatedThemeTogglerProps) {
  const buttonRef = useRef<HTMLButtonElement>(null);
  const running = useRef(false);
  const reduceMotion = useReducedMotion();
  const [darkMode, setDarkMode] = useState(false);

  useEffect(() => {
    const root = document.documentElement;
    try {
      const saved = localStorage.getItem("theme");
      if (saved === "dark" || saved === "light") {
        root.classList.toggle("dark-theme", saved === "dark");
        root.classList.toggle("light-theme", saved === "light");
      }
    } catch { /* Storage may be disabled. */ }
    const syncTheme = () => setDarkMode(root.classList.contains("dark-theme"));
    syncTheme();
    const observer = new MutationObserver(syncTheme);
    observer.observe(root, { attributes: true, attributeFilter: ["class"] });
    return () => observer.disconnect();
  }, []);

  const onToggle = useCallback(async () => {
    if (!buttonRef.current || running.current) return;
    const root = document.documentElement;
    const nextDark = !root.classList.contains("dark-theme");
    const apply = () => {
      flushSync(() => {
        setDarkMode(nextDark);
        root.classList.toggle("dark-theme", nextDark);
        root.classList.toggle("light-theme", !nextDark);
      });
      try { localStorage.setItem("theme", nextDark ? "dark" : "light"); }
      catch { /* The theme still changes without storage. */ }
    };
    if (!document.startViewTransition || reduceMotion) {
      apply();
      return;
    }
    const { left, top, width, height } = buttonRef.current.getBoundingClientRect();
    const x = left + width / 2;
    const y = top + height / 2;
    const radius = Math.hypot(Math.max(x, innerWidth - x), Math.max(y, innerHeight - y));
    running.current = true;
    root.classList.add("theme-transitioning");
    let transition: ReturnType<Document["startViewTransition"]> | undefined;
    try {
      transition = document.startViewTransition(apply);
      await transition.ready;
      await root.animate(
        { clipPath: [`circle(0px at ${x}px ${y}px)`, `circle(${radius}px at ${x}px ${y}px)`], filter: ["brightness(0.85)", "brightness(1)"] },
        { duration: 900, easing: "ease-in-out", pseudoElement: "::view-transition-new(root)" },
      ).finished;
      await transition.finished;
    } catch {
      transition?.skipTransition();
      apply();
    } finally {
      root.classList.remove("theme-transitioning");
      running.current = false;
    }
  }, [reduceMotion]);

  return (
    <button
      ref={buttonRef}
      onClick={onToggle}
      aria-label="Modo oscuro"
      role="switch"
      aria-checked={darkMode}
      title={darkMode ? "Cambiar a modo claro" : "Cambiar a modo oscuro"}
      className={cn("flex size-11 cursor-pointer items-center justify-center rounded-full p-2 text-black outline-offset-4 focus-visible:outline-2 dark:text-white", className)}
      type="button"
    >
      <AnimatePresence mode="wait" initial={false}>
        <motion.span
          key={darkMode ? "sun" : "moon"}
          initial={reduceMotion ? false : { opacity: 0, scale: 0.55, rotate: darkMode ? 25 : -25 }}
          animate={{ opacity: 1, scale: 1, rotate: 0 }}
          exit={{ opacity: 0 }}
          transition={{ duration: reduceMotion ? 0 : 0.33 }}
          aria-hidden="true"
        >
          {darkMode ? <Sun /> : <Moon />}
        </motion.span>
      </AnimatePresence>
    </button>
  );
}
