# Smart Deal Finder - Frontend

The frontend for **Smart Deal Finder** is built with [Next.js](https://nextjs.org) and [Tailwind CSS](https://tailwindcss.com). It provides a responsive, dark-mode enabled interface for managing and visualizing supermarket deals extracted by AI.

## 🚀 Key Features

- **Admin Dashboard**: `/admin`
  - **Batch Upload**: Drag-and-drop flyers for processing.
  - **Analytics**: View extraction confidence and model performance.
  - **Settings**: Configure AI models and system preferences.
- **Deal Feed**: Main view showing extracted product cards with prices and discounts.
- **Responsive Design**: optimized for both Desktop and Mobile web.

## 🛠️ Scripts

In the project directory, you can run:

### `npm run dev`
Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

The page will reload when you make changes.\
You may also see any lint errors in the console.

### `npm run build`
Builds the app for production to the `.next` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

### `npm run start`
Starts the production server after building.

## 📂 Structure

- `src/app`: App Router pages (`page.tsx`, `layout.tsx`).
  - `admin/`: Admin dashboard routes.
- `src/components`: Reusable UI components.
  - `ui/`: Fundamental building blocks (Buttons, Cards, Modals).
  - `views/`: specific page sections (`DealsView`, `SettingsTab`).
- `src/lib`: Utility functions and API clients (`api.ts`).

## ⚙️ Configuration

The frontend interacts with the backend via a reverse proxy configured in `next.config.ts`:

```typescript
// next.config.ts
rewrites: async () => [
  {
    source: '/api/:path*',
    destination: 'http://127.0.0.1:8000/api/:path*', // Hooks up to FastAPI
  },
]
```
This ensures no CORS issues and simplifies mobile access via LAN.
