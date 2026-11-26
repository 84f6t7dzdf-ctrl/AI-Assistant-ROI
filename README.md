# AI-Assistant-ROI
A company wants to know whether rolling out an AI assistant (such as Claude for Work) to its staff pays for itself

This repo is a small Streamlit app that models the first 12 months of a rollout. You change the assumptions in the sidebar, and the page shows net value, ROI, payback month, break-even hours and a chart of cumulative net value.

## Run it on your computer

You need Python 3.9 or newer. To check, open a terminal (Terminal on Mac, PowerShell on Windows) and run `python3 --version` (on Windows, `python --version`). If it isn't installed, get it from [python.org/downloads](https://www.python.org/downloads/).

1. **Download the code.** Either run `git clone https://github.com/84f6t7dzdf-ctrl/AI-Assistant-ROI.git`, or on GitHub click **Code → Download ZIP** and unzip it.
2. **Open a terminal in that folder.** For example: `cd AI-Assistant-ROI`
3. **Create a virtual environment** (a private space for this project's packages). You only do this once.
   - Mac/Linux: `python3 -m venv .venv` then `source .venv/bin/activate`
   - Windows: `python -m venv .venv` then `.venv\Scripts\activate`
4. **Install the packages.** Run `pip install -r requirements.txt`
5. **Start the app.** Run `streamlit run app.py`. Your browser opens at http://localhost:8501. If it doesn't, paste that address into your browser.

Press `Ctrl+C` in the terminal to stop the app. Next time, you only need step 2, the `activate` command from step 3, and step 5.

## Run the tests

With the virtual environment active, run `pytest`. The tests check the calculations against numbers worked out by hand.

## Files

- `assumptions.py`: the default inputs. Each one is an estimate.
- `logic.py`: the calculations, with no Streamlit code in it.
- `app.py`: the Streamlit page.
- `tests/test_logic.py`: the tests, with the hand working at the top.

## How the model works

- **Month 0** holds only the one-off cost: rollout plus training time (training hours × hourly cost × staff).
- **Months 1 to 12** each have a benefit and a running cost.
  - Benefit = staff × adoption × hours saved per week × working weeks ÷ 12 × hourly cost × realisation.
  - Running cost = staff × licence per seat + admin. Licences are paid for every seat, not just active users.
- **Adoption** ramps up in a straight line to its target over the ramp-up months. With a 3-month ramp and a 60% target, that's 20%, 40%, then 60% from month 3 onwards.
- **ROI** = net value ÷ total cost, over months 0 to 12.
- **Payback month** is the first month where cumulative net value reaches zero or more.
- **Break-even hours** is the hours saved per user per week that would make the 12-month net value exactly zero, with everything else unchanged.
