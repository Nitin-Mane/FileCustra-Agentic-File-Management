# FileCustra Frontend (React 19 + TypeScript + Vite)

This directory contains the user interface layer of FileCustra, built with **React 19**, **TypeScript**, **Vite**, and custom **Prism Material CSS** design tokens.

---

## Workspace Views & Routes

- **SplashView:** 5-second animated startup loading screen with hardware diagnostic progress.
- **WelcomeView:** Privacy-first onboarding screen detailing local execution guarantees.
- **DriveDashboardView:** System Drives Analytics Dashboard (`C:\`, `D:\`, `E:\` storage meters and GPU VRAM gauge).
- **OnboardingSetupView:** One-time local model download & hardware tuning wizard.
- **HomeView:** Workspace hub displaying recent activity, active model status, and module shortcuts.
- **DiscoveryView:** File discovery table with Google Magika labels, SHA-256 hashes, and Tesseract OCR indicators.
- **ConstellationView:** 60 FPS Canvas particle visualizer rendering real-time sidecar IPC events.
- **AutoAiView:** Auto AI topology strategy planner supporting 4 folder organization topologies.
- **TerminalView:** Interactive ReAct CLI Terminal Console displaying Chain-of-Thought (CoT) reasoning traces and RL reward scores.
- **GuidedQueryView:** 5-question step-by-step interactive interview wizard.
- **OperationPlanView:** Dry-run simulation tree diff viewer with collision resolution toggles.
- **JournalUndoView:** Transaction journal history viewer with 1-click reverse rollback trigger.
- **ModelManagerView:** Local model catalog downloader and LiteRT-LM runtime benchmark scores.
- **SettingsView:** Personalization memory inspector, Hardware Privacy Lock toggle, and diagnostic controls.

---

## Development Scripts

```bash
# Install Node dependencies
npm install

# Launch Vite development server
npm run dev

# Type check & build production bundle
npm run build
```
