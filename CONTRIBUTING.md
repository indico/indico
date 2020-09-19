# Contributing to Indico

Contributing to Indico can mean so much more than writing code! There are many other activities you can help with, all of them no less important than writing some amazing Python code or a shiny React component. This is a list of the main ways in which you can help us.

### Bug hunting

 * :beetle: Have you found a bug? Do you have a feature to suggest?
   - First of all, check whether there isn't already a similar issue;
   - If not, [open a GitHub issue](https://github.com/indico/indico/issues/new);
   - *Please, follow the default templates we provide, they make things much easier!* 
 * 🚨 Have you found a security issue? → E-mail us at [indico-team@cern.ch](mailto:indico-team@cern.ch)

### Translation :earth_asia:

Would you like to to help us translate Indico to your language?

 * First of all, check the [I18n section of our forum](https://talk.getindico.io/c/i18n):
   * If your language is already listed, annouce yourself in the corresponding thread;
   * If your language is not listed, create a new post for it, following [the same style of the previous ones](https://talk.getindico.io/t/japanese-ja-translation-group/542?u=pferreir);
 * Then, [create an account on Transifex](https://www.transifex.com/indico/indico/) and ask to join the corresponding team in the `indico` project;
 * Someone from the team will be in contact with you as soon as possible;

### Documentation :pencil: 

 * ❌ Have you found a typo, mistake, wrong information or an outdated screenshot?
 * :muscle: Do you think you can help us write better documentation or document a part of Indico that is not documented at all?
 * Contact us at [indico-team@cern.ch](mailto:indico-team@cern.ch), so that we can get things started!

### Code :wrench:

 * Have you got a particular ticket in mind? Answer to it letting us know that you would like to help. We will be glad to discuss a possible implementation approach with you.
 * Would you like to help but you're not sure with what? Look for [issues with the `help wanted` tag](https://github.com/indico/indico/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22) and choose one that suits your experience with Indico and the technologies we use. Then, let us know you'd like to help with it (by answering to it)!
 * *Please always ping us before you start working on something that you believe will take a significant amount of time!*

## Making a Pull Request


> :warning:When submitting a Pull Request to this project for something more than a typo or small bug, **please make sure your idea was discussed beforehand** with the development team, via an [issue](https://github.com/indico/indico/issues/new/choose) or the [forum](https://talk.getindico.io).

Open Source is about contributing back, but it's important to know how to do it in the best way possible. We don't want you to spend your precious time in a "ping-pong" of code reviews that will end up not being fun. We also want to maximize the chances that your contribution will already be done in the "Indico way" and following what we consider good practices.

This checklist is meant to help you follow those practices:

 * :full_moon: Make sure your code is complete:
   - [ ] Have you added **docstrings** to newly created classes?
   - [ ] Have you added [**jsdoc** strings](https://react-styleguidist.js.org/docs/documenting.html) to new React components?
   - [ ] Have you added **code comments** in parts that are harder to understand?
   - [ ] Have you checked that you haven't forgotten to add any **newly created files** to the Git repo?
   - [ ] Have you added **unit tests** to trickier parts of the Python code?

 * :white_check_mark: Make sure your code has no errors:
    - [ ] **Code style and formatting** - have you run `eslint`, `flake8` and `pydocstyle` (or the [pre-commit hook](https://github.com/indico/indico/blob/master/pre-commit.githook))?
    - [ ] **Regressions** - have you tried running the unit tests? (`pytest`)

* :loudspeaker: Make sure others understand what has changed:
  - [ ] Log any feature changes and bug fixes in `CHANGES.rst` (**changelog** for developers)
  - [ ] **Update the documentation** if needed
  - [ ] Check that your contribution is split in **logically separate commits** (one commit for one thing);
  - [ ] Check that your **commit messages** are clear and contain no typos. The subject message should be in the [**imperative mood**](https://chris.beams.io/posts/git-commit/);

* ⚖️ Make sure you have the **right to contribute** what you want to contribute. It should be either:
  - **original work**
  *OR*
  - **properly attributed** and in accordance with the **original license**. Please note that you **cannot** include any GPL/AGPL code!

## Code of Conduct

Indico is a CERN project and is thus subject to [CERN's Code of Conduct](https://hr.web.cern.ch/codeofconduct). Outside contributors are expected to act in accordance with the principles of the CoC that apply to them.
The development team commits to ensuring that [CERN's values](https://hr.web.cern.ch/cerns-values) are respected and reserves the right to suspend from the community any contributors that are found to be engaged in harmful behaviour. Personal attacks or any other form of harassment will not be tolerated.

