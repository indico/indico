/* This file is part of Indico.
 * Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 3 of the
 * License, or (at your option) any later version.
 *
 * Indico is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Indico; if not, see <http://www.gnu.org/licenses/>.
 */

const flaskURLPlugin = ({types: t, template}, opts) => {
    const buildFunc = template.expression('FUNC.bind(null, RULE)');
    const importPrefix = opts.importPrefix || 'flask-url';
    const funcName =  opts.funcName || 'build_url';
    const urlMap = opts.urlMap || {};
    const importRegex = new RegExp(`^${opts.importPrefix}:(.+)$`);

    return {
        visitor: {
            ImportDeclaration: {
                exit(path) {
                    const importTarget = path.node.source.value;
                    const match = importTarget.match(importRegex);
                    if (!match) {
                        return;
                    }
                    const endpoint = match[1];
                    if (path.node.specifiers.length === 0) {
                        throw path.buildCodeFrameError(
                            `${importPrefix} imports must use a default import`
                        );
                    } else if (path.node.specifiers.length > 1) {
                        throw path.get('specifiers.1').buildCodeFrameError(
                            `${importPrefix} imports must use exactly one import`
                        );
                    } else if (!t.isImportDefaultSpecifier(path.node.specifiers[0])) {
                        throw path.get('specifiers.0').buildCodeFrameError(
                            `${importPrefix} imports must use a default import`
                        );
                    }
                    const importName = path.node.specifiers[0].local.name;
                    const data = urlMap[endpoint];
                    if (!data) {
                        throw path.get('source').buildCodeFrameError(
                            `${importPrefix} imports must reference a valid flask endpoint`
                        );
                    }

                    const variable = t.variableDeclarator(
                        t.identifier(importName),
                        buildFunc({FUNC: funcName, RULE: t.valueToNode(data)})
                    );
                    path.replaceWith({
                        type: 'VariableDeclaration',
                        kind: 'const',
                        declarations: [variable],
                        leadingComments: [
                            {
                                type: 'CommentBlock',
                                value: ` flask url builder for '${endpoint}' `
                            }
                        ]
                    });
                }
            }
        }
    };
};


export default flaskURLPlugin;
