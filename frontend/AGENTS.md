# Frontend Agent Guide

This document describes the current frontend implementation in `frontend/`.

## Purpose

- Current frontend is a standalone Next.js Kanban demo.
- It is currently client-side and in-memory only (no backend persistence yet).
- It already includes unit and e2e tests.

## Stack

- Next.js 16 (App Router)
- React 19
- TypeScript
- Tailwind CSS v4
- `@dnd-kit` for drag-and-drop
- Vitest + Testing Library for unit/component tests
- Playwright for e2e tests

## Scripts

- `npm run dev` - run local Next.js dev server
- `npm run build` - production build
- `npm run start` - run built app
- `npm run lint` - ESLint
- `npm run test:unit` - unit/component tests (Vitest)
- `npm run test:e2e` - browser e2e tests (Playwright)
- `npm run test:all` - unit + e2e

## App Structure

- `src/app/layout.tsx`
  - Global layout, metadata, and font setup (`Space_Grotesk`, `Manrope`).
- `src/app/page.tsx`
  - Home page renders `AuthGate`.
- `src/app/globals.css`
  - Defines project color tokens and visual primitives.

## Domain Model (`src/lib/kanban.ts`)

- Types:
  - `Card` (`id`, `title`, `details`)
  - `Column` (`id`, `title`, `cardIds`)
  - `BoardData` (`columns`, `cards`)
- `initialData`
  - 5 fixed starter columns and initial seed cards.
- `moveCard(columns, activeId, overId)`
  - Core board reordering/move logic.
  - Supports reorder within column and move across columns.
  - Supports dropping onto column container (append to end).
- `createId(prefix)`
  - Generates local IDs for new cards.

## Components

- `src/components/AuthGate.tsx`
  - Checks session on initial load via `/api/auth/me`.
  - Shows login form for unauthenticated users.
  - Logs in using `/api/auth/login` with fixed credentials.
  - Provides logout action via `/api/auth/logout`.
  - Renders `KanbanBoard` only for authenticated users.

- `src/components/KanbanBoard.tsx`
  - Main board container and state owner.
  - Holds `board` and `activeCardId` state.
  - Handles drag start/end using `DndContext`.
  - Implements:
    - Column rename
    - Add card
    - Delete card
    - Card move/reorder
  - Renders five `KanbanColumn` components and drag overlay preview.

- `src/components/KanbanColumn.tsx`
  - Column UI shell.
  - Uses `useDroppable` and `SortableContext`.
  - Column title is directly editable via input.
  - Renders card list, empty-state hint, and `NewCardForm`.

- `src/components/KanbanCard.tsx`
  - Sortable card item with drag bindings (`useSortable`).
  - Shows title/details and remove button.

- `src/components/NewCardForm.tsx`
  - Local open/close form state.
  - Validates non-empty title, trims values, emits `onAdd`.

- `src/components/KanbanCardPreview.tsx`
  - Lightweight visual preview rendered inside drag overlay.

## Testing Coverage

- Unit/component:
  - `src/components/AuthGate.test.tsx`
    - Shows sign-in form when unauthenticated.
    - Signs in and renders board.
    - Shows invalid-credentials error.
  - `src/lib/kanban.test.ts`
    - Reorder in same column.
    - Move between columns.
    - Drop to end of column.
  - `src/components/KanbanBoard.test.tsx`
    - Renders 5 columns.
    - Renames column.
    - Adds and removes card.

- E2E:
  - `tests/kanban.spec.ts`
    - Login flow renders board.
    - Add card flow works.
    - Drag/drop card between columns works.
    - Logout returns to sign-in.

## Current Limitations

- Auth is MVP-only (hardcoded credentials).
- Board state is still local/in-memory once logged in.
- No backend board persistence yet.
- No AI chat UI yet.

## Constraints for Upcoming Work

- Keep UX simple and avoid feature creep.
- Preserve existing design token usage from `globals.css`.
- Keep tests updated for every behavioral change.
- As backend integration is added, keep static-export compatibility for frontend output.