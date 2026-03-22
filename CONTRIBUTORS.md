# Contributors

## 🎯 Project Creator & Lead Maintainer

**Kay Beißert** ([kbeissert](https://github.com/kbeissert))

- **Role**: Original Author, Lead Developer, Project Owner
- **Period**: 2025 – present
- **Contributions**:
  - Designed and built CrucibleMark from concept to v3.0.1
  - Developed all benchmark modules: Code Quality, UX Writing, Documentation,
    Content Transformation, Reasoning, Political Compass, Cultural Intelligence
  - Architected the modular plugin system
  - Implemented the Golden Standard methodology
  - Built with AI assistance (GitHub Copilot, Google Gemini, Claude Sonnet 4.5,
    Perplexity AI)

---

## 🤖 AI-Assisted Development

This project demonstrates what's possible when human creativity meets AI assistance.

### Development Tools Used

- **GitHub Copilot** – Code completion, refactoring, boilerplate generation
- **Google Gemini 3.1 Pro** via GitHub Copilot – Python development & refactoring
- **Anthropic Claude Sonnet 4.5** via GitHub Copilot – Architecture & code review
- **Perplexity AI** – Research, architecture consulting & documentation

### Benchmark Architecture

CrucibleMark uses a two-model evaluation pipeline:

- **LLM Judge: Anthropic Claude Haiku 4.5** – Scores individual benchmark responses.
  Chosen for instruction-following accuracy and consistent, pedantic evaluation.
- **Reviewer: Google Gemini 2.5 Pro** – Aggregates all reports into a final analysis.
  The 200.000 token context window handles full report sets in a single pass.

Both models are used consistently within their respective roles. Mixing judge models
distorts scores – all results in the leaderboard were evaluated by Claude Haiku 4.5.

**Note**: All AI-generated code was reviewed, tested, and integrated by the human
creator. CrucibleMark is the result of human vision and judgment – AI was the tool,
not the author.

---

## 🌍 Community Contributors

Want to contribute? See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Contributors (Alphabetical)

*(No external contributors yet – be the first!)*

---

## 🙏 Acknowledgments

Special thanks to:

- **Ollama Team** – For making local LLM inference accessible
- **Sentence Transformers / UKP Lab** – For the semantic similarity engine
- **Open Source Community** – For the tools and libraries that made this possible

---

## 📜 Licensing

All contributions to CrucibleMark must be licensed under the
**Apache License 2.0** (see [LICENSE](LICENSE)).

By contributing, you agree that your contributions will be licensed
under the same terms.

---

## 📧 Contact

**Project Owner**: Kay Beißert

- Email: [kay.b@media-garage.de](mailto:kay.b@media-garage.de)
- GitHub: [kbeissert](https://github.com/kbeissert)
- Website: [www.media-garage.de](https://www.media-garage.de)

---

**Last Updated**: March 2026
