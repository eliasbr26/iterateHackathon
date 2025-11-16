# css-dependency

A css parser for getting imports from css code.

```bash
npm install css-dependency
```

```ts
import { parse } from "css-dependency";

const imports = parse('@import "./example.css";');

assert.deepStrictEqual(imports.unwrap(), [
	{
		directive: "@import",
		module: "./util.css",
		raw: '@import "./util.css";',
	},
]);
```

## Supported Syntax

```css
@import "./example.css";
@import url("./something.css");
@import "./example.css" /* Conditions... */;
```

### Tailwind Directives

In `tailwindcss@v4` more @ directives were introduced that can result in additional dependencies for your css files. You can enable their detection by setting `allowTailwindDirectives` to true:

```ts
import { parse } from "css-dependency";

parse(code, { allowTailwindDirectives: true });
```

#### Supported Directives

```ts
["@plugin", "@config", "@reference"];
```
