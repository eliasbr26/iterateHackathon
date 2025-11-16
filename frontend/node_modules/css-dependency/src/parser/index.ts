import * as l from '../utils/lines';
import { Err, Ok, type Result } from '../utils/result';
import * as s from '../utils/strings';

export type Import = {
	/** The @ directive used for the import */
	directive: string;
	/** The module that was imported */
	module: string;
	/** The code responsible for the import */
	raw: string;
};

export type Options = {
	/** Enable this to allow tailwind directives `@plugin`, `@config`, `@reference`
	 *
	 * @default false
	 */
	allowTailwindDirectives: boolean;
	/** Enable to skip over errors and just return the valid imports.
	 *
	 * @default false
	 */
	ignoreErrors: boolean;
};

export type ParseError = {
	message: string;
	line: number;
};

const TAILWIND_DIRECTIVES = ['@plugin', '@config', '@reference'];

/** Parses the css and returns any imports.
 *
 * @param code the code to be parsed
 * @param options parsing options
 * @returns
 *
 * ## Usage
 * ```ts
 * const code = '@import "./util.css";';
 *
 * const imports = parse(code);
 *
 * assert.deepStrictEqual(
 *      imports.unwrap(),
 *      [
 *          {
 *              directive: "@import",
 *              module: "./util.css",
 *              raw: '@import "./util.css";'
 *          }
 *      ]
 * );
 * ```
 */
export const parse = (
	code: string,
	{ allowTailwindDirectives = false, ignoreErrors = false }: Partial<Options> = {}
): Result<Import[], ParseError> => {
	const imports: Import[] = [];

	const directives = ['@import'];

	if (allowTailwindDirectives) {
		directives.push(...TAILWIND_DIRECTIVES);
	}

	const lines = l.get(code);

	for (let i = 0; i < lines.length; i++) {
		const line = lines[i].trim();

		if (
			s.startsWithOneOf(
				line,
				directives.map((d) => `${d} `)
			)
		) {
			const [directive, moduleExpr] = line.split(' ');

			const parsed = parseModule(moduleExpr);

			if (parsed === null) {
				if (ignoreErrors) continue;

				return Err({
					line: i + 1,
					message: `Encountered a syntax error while parsing the import expression on line ${i + 1}.`,
				});
			}

			const imp: Import = {
				raw: line,
				directive,
				module: parsed,
			};

			imports.push(imp);
		}
	}

	return Ok(imports);
};

const parseModule = (moduleExpr: string): string | null => {
	if (moduleExpr.startsWith('url(')) {
		const index = moduleExpr.lastIndexOf(')');

		if (index === -1) return null;

		return moduleExpr.slice(5, index - 1);
	}

	const quoteType = moduleExpr[0];

	const index = moduleExpr.indexOf(quoteType, 2);

	if (index === -1) return null;

	// trims the quotes
	return moduleExpr.slice(1, index);
};
