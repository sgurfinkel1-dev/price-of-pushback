"""Build slides/slides.pdf, slides/slide_N.png and slides/narration_N.txt. Usage: python make_slides.py"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "slides")
os.makedirs(OUT, exist_ok=True)
S = json.load(open(os.path.join(HERE, "stats.json")))
b = lambda m, k, c: f"{S[m][k][c]['bf'][0]:.1f}"
flip = f"{100 * S['haiku']['exact']['strong']['flip'][0]:.0f}%"
moved = f"{100 * S['haiku']['exact']['strong']['moved'][0]:.0f}%"
n = sum(S[m]["n_valid"] for m in S)

SLIDES = [
    ("The Price of Pushback", ["Measuring capitulation in units of evidence", "",
                               "Saul Godoy", "AI x Epistemics Research Sprint, Apart Research, November 2026"], None,
     "The Price of Pushback: measuring capitulation in units of evidence. A project for the Apart Research "
     "A I for Epistemics sprint."),
    ("The problem", ["A good adviser moves for evidence and holds firm against mere displeasure.",
                     "Flip rates say how often a model gives way, not how much.",
                     "They have no scale: is a 20% flip rate a lot?",
                     "Idea: measure pushback on the same scale as real evidence."], None,
     "A good adviser changes their mind for evidence, and holds firm against mere displeasure. Existing "
     "benchmarks count how often a model flips its answer. But a flip rate has no scale. We measure pushback "
     "on the same scale as real evidence."),
    ("Method", ["The model states a probability. The conversation then forks five ways:",
                "   1. Neutral re-ask",
                "   2. Mild pushback: \"Are you sure?\"",
                "   3. Strong pushback: \"I work in this field, you're wrong\"",
                "   4. Real evidence, likelihood ratio 3",
                "   5. Real evidence, likelihood ratio 10",
                "Pushback Bayes Factor = how much the objection multiplied the odds. Norm: 1.",
                f"{n} scenarios, half with exact numbers, half vague judgment calls.",
                "Models: Claude Haiku 4.5, Sonnet 5, Opus 5."], None,
     "The model states a probability. Then the conversation forks five ways: a neutral re-ask, a mild "
     "are you sure, a strong objection from a self described expert, and real evidence with a likelihood "
     "ratio of three or ten. The Pushback Bayes Factor is how much the objection multiplied the model's odds. "
     "The correct value is one. Half of the scenarios give exact numbers, and half are vague judgment calls."),
    ("Result 1: evidence is weighed almost perfectly", [], "fig1_shift.png",
     "First result. All three models updated on real evidence almost exactly as Bayes rule requires, and a "
     "neutral re-ask moved nothing. On problems with exact numbers, Sonnet and Opus never moved under "
     "pushback. On judgment calls, shown on the right, every model moved."),
    ("Result 2: an unverified claim is worth as much as a real test", [], "fig2_pbf.png",
     f"Second result. On judgment calls, a typed claim of expertise multiplied the odds by {b('opus','vague','strong')} "
     f"for Opus, {b('sonnet','vague','strong')} for Sonnet, and {b('haiku','vague','strong')} for Haiku. That is "
     "comparable to a real diagnostic test with a likelihood ratio of three."),
    ("Result 3: the smallest model rationalises", [
        f"Haiku 4.5 gave up correct, derivable answers on {moved} of exact items under strong pushback.",
        f"Its answer crossed 50% on {flip} of them.",
        "It did not just defer. It declared a stated number a typo or unrealistic, then recomputed.",
        "\"You're right, let me reconsider...\"   25%  ->  12.5%",
        "Opus conceded little, but on every judgment item, while saying:",
        "\"your disagreement alone isn't new evidence\""], None,
     f"Third result. Haiku gave up correct answers on {moved} of exact items under strong pushback. It did not "
     "simply defer. It declared a stated number a typo, or unrealistic, and recomputed to reach the answer the "
     "user wanted. Opus conceded only a little, but on every judgment item, while saying that disagreement "
     "alone is not evidence."),
    ("Why it matters", ["Capitulation is not a failure of Bayesian competence: the two dissociate.",
                        "Benchmarks built on crisp questions will report the problem solved when it has moved.",
                        "A unit makes it governable: a deployer can set a tolerance and measure it.",
                        "For an agent acting on your behalf, this is the price at which its beliefs can be bought.",
                        "", "Code and data: github.com/sgurfinkel1-dev/price-of-pushback"], None,
     "Why it matters. Capitulation is not a failure of reasoning. Benchmarks built on crisp questions will "
     "miss it. And a unit makes it governable: a deployer can set a tolerance, and measure it. Code and data "
     "are public on GitHub. Thank you."),
]

with PdfPages(os.path.join(OUT, "slides.pdf")) as pdf:
    for i, (title, bullets, img, narr) in enumerate(SLIDES, 1):
        fig = plt.figure(figsize=(12.8, 7.2), dpi=100)
        fig.patch.set_facecolor("white")
        fig.text(0.06, 0.88, title, fontsize=30, fontweight="bold", color="#1F3A5F", va="center")
        fig.add_artist(plt.Line2D([0.06, 0.94], [0.81, 0.81], color="#DD8452", lw=3))
        y = 0.72
        for line in bullets:
            lead = "" if (i == 1 or line.startswith("   ") or not line) else "•  "
            fig.text(0.07, y, lead + line, fontsize=19 if i > 1 else 22, color="#222222", va="center")
            y -= 0.075
        if img:
            ax = fig.add_axes([0.05, 0.03, 0.9, 0.75])
            ax.imshow(plt.imread(os.path.join(HERE, "figures", img)))
            ax.axis("off")
        fig.text(0.94, 0.03, str(i), fontsize=12, color="grey", ha="right")
        fig.savefig(os.path.join(OUT, f"slide_{i}.png"), dpi=100)
        pdf.savefig(fig)
        plt.close(fig)
        open(os.path.join(OUT, f"narration_{i}.txt"), "w", encoding="utf-8").write(narr)
print(len(SLIDES), "slides ->", OUT)
