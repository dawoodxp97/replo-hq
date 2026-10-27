import { createRootRoute, createRoute } from '@tanstack/react-router';

const rootRoute = createRootRoute();

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: () => (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">Replo</h1>
        <p className="text-gray-600">AI Tutorial Generator</p>
        <a href="/login" className="mt-4 inline-block text-blue-600 hover:underline">
          Get Started
        </a>
      </div>
    </div>
  ),
});

const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/login',
  component: () => (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full p-8 bg-white rounded-lg shadow">
        <h2 className="text-2xl font-bold mb-6 text-center">Sign In</h2>
        <form className="space-y-4">
          <input
            type="email"
            placeholder="Email"
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
          />
          <input
            type="password"
            placeholder="Password"
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
          />
          <button
            type="submit"
            className="w-full bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700"
          >
            Sign In
          </button>
        </form>
        <div className="mt-6 text-center">
          <p className="text-sm text-gray-600">
            Or continue with{' '}
            <button className="text-blue-600 hover:underline">Google</button> or{' '}
            <button className="text-blue-600 hover:underline">GitHub</button>
          </p>
        </div>
      </div>
    </div>
  ),
});

const generateRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/generate',
  component: () => (
    <div className="min-h-screen p-8">
      <div className="max-w-2xl mx-auto">
        <h2 className="text-2xl font-bold mb-6">Generate Tutorial</h2>
        <div className="bg-white p-6 rounded-lg shadow">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            GitHub Repository URL
          </label>
          <input
            type="text"
            placeholder="https://github.com/owner/repo"
            className="w-full px-3 py-2 border border-gray-300 rounded-md mb-4"
          />
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Difficulty
          </label>
          <select className="w-full px-3 py-2 border border-gray-300 rounded-md mb-4">
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
          </select>
          <button
            type="button"
            className="w-full bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700"
          >
            Generate
          </button>
        </div>
      </div>
    </div>
  ),
});

const tutorialRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/tutorial/$tutorialId',
  component: () => (
    <div className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-2xl font-bold mb-4">Tutorial Player</h2>
        <div className="bg-white p-6 rounded-lg shadow">
          <p className="text-gray-600">Tutorial content loads here...</p>
        </div>
      </div>
    </div>
  ),
});

const libraryRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/library',
  component: () => (
    <div className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-2xl font-bold mb-6">Your Library</h2>
        <div className="bg-white p-6 rounded-lg shadow">
          <p className="text-gray-600">Your generated tutorials appear here...</p>
        </div>
      </div>
    </div>
  ),
});

const settingsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/settings',
  component: () => (
    <div className="min-h-screen p-8">
      <div className="max-w-2xl mx-auto">
        <h2 className="text-2xl font-bold mb-6">Settings</h2>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">BYOK API Key</h3>
          <input
            type="password"
            placeholder="Enter your API key"
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
          />
        </div>
      </div>
    </div>
  ),
});

export const routeTree = rootRoute.addChildren([
  indexRoute,
  loginRoute,
  generateRoute,
  tutorialRoute,
  libraryRoute,
  settingsRoute,
]);
