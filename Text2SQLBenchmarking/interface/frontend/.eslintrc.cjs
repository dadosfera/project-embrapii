module.exports = {
  env: { browser: true, es2021: true },
  extends: ["eslint:recommended"],
  parser: "@typescript-eslint/parser",
  parserOptions: { ecmaVersion: 2021, sourceType: "module" },
  plugins: ["react-hooks"],
  rules: {
    "no-unused-vars": "off",
    "no-undef": "off",
    "react-hooks/rules-of-hooks": "error",
    "react-hooks/exhaustive-deps": "warn"
  },
  ignorePatterns: ["dist", "node_modules"]
};
