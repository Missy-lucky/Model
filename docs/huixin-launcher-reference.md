# Huixin Launcher reference mapping

Date: 2026-10-10

## Reference project

Repository: <https://github.com/XnneHangLab/HuixinLauncherTemplate>

The project describes itself as a Tauri 2 + React + TypeScript desktop launcher template inspired by the Huixin launcher style. Its useful value is not a single screen; it is the complete launcher architecture:

```text
shell
+ navigation
+ topbar
+ home page
+ settings page
+ model/resource page
+ console page
+ runtime event bridge
+ serial download queue
+ managed folders
```

The repository does not declare a license. LongY Studio therefore does not copy its source, assets, text, or artwork. This document records the architecture and visual hierarchy independently and maps those concepts to an original PySide6 implementation.

## Observed architecture

### App shell

Reference files:

- `src/layouts/AppShell/AppShell.tsx`
- `src/components/navigation/Sidebar/Sidebar.tsx`
- `src/components/window/Topbar/Topbar.tsx`

The shell uses:

- a narrow left navigation rail
- a separate top bar
- a routed page area
- a persisted day/night theme
- one runtime-state container feeding all pages

### Home page

Reference files:

- `src/pages/HomePage/HomePage.tsx`
- `src/components/home/HeroBanner/HeroBanner.tsx`
- `src/components/home/FolderGrid/FolderGrid.tsx`
- `src/components/home/NoticePanel/NoticePanel.tsx`

The home page is a launcher surface rather than a settings form:

- large visual hero
- managed folder cards
- notices
- a prominent run button
- status chips

### Resource and queue page

Reference files:

- `src/pages/ModelsPage/ModelsPage.tsx`
- `src/components/models/ModelCard/ModelCard.tsx`
- `src/styles/models.css`

The page separates:

- resource cards
- readiness state
- hardware requirement
- serial task queue
- per-file progress

### Console page

Reference files:

- `src/pages/ConsolePage/ConsolePage.tsx`
- `src/styles/console.css`

It provides:

- current status pill
- runtime driver
- active task
- raw and structured event logs
- clear/copy/export controls
- auto-scroll and wrap toggles

### Settings and environment

Reference files:

- `src/pages/SettingsPage/SettingsPage.tsx`
- `src/styles/settings.css`

It provides:

- environment status summary
- workspace root selection
- runtime driver selection
- Python path selection
- save-and-reprobe behavior

### Runtime architecture

Reference files:

- `src/services/runtime/runtime.ts`
- `src/services/runtime/bridge.ts`
- `src-tauri/src/runtime/state.rs`
- `src-tauri/src/runtime/process.rs`
- `src-tauri/src/runtime/commands.rs`

Important patterns:

- environment probe has explicit statuses, not booleans scattered across the UI
- resource tasks have a serial queue and one worker
- task state is updated with progress and messages
- raw logs and structured events are separate channels
- workspace switching is blocked while tasks are active
- managed folders are addressed by stable keys rather than raw paths

## Mapping into LongY Studio

| Reference concept | LongY Studio implementation |
| --- | --- |
| Narrow navigation rail | `PAGE_KEYS`, `PAGE_ICONS`, 88px sidebar in `desktop_app.py` |
| Launcher home page | `create_home()` and `render_home()` |
| Hero banner | Original `HeroCard`, using a project-generated garment background |
| Managed folder cards | Clickable environment cards for runtime, model, product, and output folders |
| Notice panel | Scrollable announcement bar and home status cards |
| One-click run | `home_run_button` -> `launch_from_home()` |
| Resource cards | Template cards with colored icons, tags, status, and run action |
| Workflow graph | Original PySide6 `WorkflowCanvas` and `CanvasNodeSpec` |
| Task queue | In-memory serial queue plus durable `workflow_runs/<product>/<recipe>/state.json` summaries |
| Console/log page | Aggregated `collect_logs()` view |
| Environment page | Backend cards and environment readiness cards |
| Runtime state | `studio_core.py` and `apparel_studio.py` |

## Visual language adopted

The reference launcher uses a dark night theme. Its screenshot family has:

- near-black shell background
- slightly elevated panels
- narrow left rail
- colored status chips
- accent-colored primary run action
- rounded cards with colored left indicators
- separate muted text and strong title text

LongY Studio now uses the same visual grammar:

```text
shell: #171B20
sidebar: #1D2228
panel: #1E242B
input: #191F25
primary accent: #F28B2C
information accent: #63B3ED
success accent: #63C8B8
warning accent: #F5A524
review accent: #EF8FB5
```

## Deliberate differences

LongY Studio does not launch a separate Gradio/WebUI process. Its first-class objects are garment products and workflow recipes. Consequently:

- Home quick actions select a workflow recipe rather than launch an external web UI.
- The workflow page is a domain-specific graph canvas rather than a generic node editor.
- Model management is represented by deterministic segmentation and optional image-edit backends.
- The queue is based on durable per-node state files so runs can be inspected after restart.

## Implementation conclusion

The mature launcher pattern is:

```text
visual shell
+ stateful environment
+ managed resources
+ serial execution
+ durable diagnostics
+ user-safe defaults
```

LongY Studio follows that structure while keeping its own clothing-production domain model and original implementation.
