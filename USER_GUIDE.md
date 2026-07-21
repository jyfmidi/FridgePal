# Fridge Pal User Guide

Welcome to Fridge Pal. This guide gets the app running locally and walks through the main experience in about five minutes.

## Quick start with Docker

### Requirements

- Git
- Docker Engine or Docker Desktop
- Docker Compose v2

### Start the app

From the repository root:

```bash
cp .env.example .env
docker compose config --quiet
docker compose up --build -d
```

Wait for both services to become healthy:

```bash
docker compose ps
curl -fsS http://127.0.0.1:8080/api/health
```

Then open [http://127.0.0.1:8080](http://127.0.0.1:8080).

### Sign in

Use the seeded local demo account:

```text
Username: demo
Password: demo12345
```

You can also create a separate account from the Register screen. Each account has its own isolated inventory and recipes.

> The sample password and secrets in `.env.example` are for local testing only. Do not use them for a public deployment.

The default `fixture` recipe mode is deterministic and requires no API keys. It is the recommended mode for a reliable local demo.

## Recommended five-minute walkthrough

### 1. Check Storage

Open **Storage** after signing in.

- **Use Soon** shows food that needs attention first.
- **Complete inventory** shows everything in the Fridge, Freezer, and Pantry.
- Use the location filters or search button to narrow the list.
- Food in Use Soon also remains in the complete inventory. It is one inventory item shown in two useful views.

### 2. Add or update food

Select **Add food**.

1. Search the Food Library or create a custom food.
2. Review the suggested location, quantity, unit, stored date, and use-by date.
3. Select **Save food**.

Back in Storage, open any food tile to inspect its lots. You can update its quantity, unit, location, stored date, or use-by date. You can also record food as used or discarded. Nothing changes until **Update storage** is confirmed.

### 3. Rescue food with AI

Open **Rescue**.

1. Select **Edit foods** or an empty `+` slot.
2. Choose up to seven foods from Storage, then select **Done**.
3. Optionally choose a cuisine.
4. Select **Find meal ideas**.

Fridge Pal generates meal ideas around the selected ingredients. Each result shows its serving size, ingredients, seasonings, and steps before you open the editor.

### 4. Edit and save a recipe

Select **Edit recipe** on a meal idea.

- Change the name, description, serving size, ingredients, or instructions.
- Try `0.5×`, **Full recipe**, or a custom portion.
- Use **Add from storage** to include another tracked ingredient.
- Select **Save to Recipes** to keep the recipe for later.

Editing a recipe never changes the inventory.

### 5. Cook and update Storage

From the Recipe Editor, select **Review use & update storage**.

The **What did you use?** screen shows the proposed amounts for the current portion. Adjust them to match what was actually used, then select **Update storage**.

This is the only point where cooking changes inventory. Fridge Pal caps deductions at the available quantity and never allows Storage to become negative.

### 6. Reuse saved recipes

Open **Recipes** to see recipes you chose to keep.

- Open a recipe to review it.
- Select **Edit** to change it.
- Select **Cook & update storage** or **Cook again** to return to the cooking flow.

### 7. Review History and Undo

Open **History**.

- The **Storage** tab records check-ins, edits, cooking, reductions, discards, and reversals.
- Use **Undo** on supported events to create a compensating change without deleting the original history.
- The **Meal Ideas** tab keeps recent Rescue results so they can be opened again.

## Other details to try

- Switch between English and Simplified Chinese from the account menu.
- Resize the browser or open the app on a phone. Mobile and desktop provide the same features.
- Try keyboard navigation and reduced-motion mode. Fridge Pal includes visible focus states, accessible labels, and reduced-motion support.

## Stop or reset the local demo

Stop the containers while keeping the database:

```bash
docker compose down
```

Start them again with:

```bash
docker compose up -d
```

To inspect a startup problem:

```bash
docker compose logs --tail=200 app db
```

For full deployment and operations guidance, see [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

## What to look for

Fridge Pal is designed around one simple loop:

```text
Track food → notice what needs using → generate a meal → cook → confirm what was used
```

The important product boundary is that AI can suggest what to cook, but it can never change inventory by itself.
