# 📊 TabMate — Expense Splitter & Group Tab Tracker

A clean, responsive web application and Python module designed to track shared group expenses, compute live net balances, and calculate minimal debt settlement transactions using a greedy balance-matching algorithm[cite: 4, 5].

🌐 **Live Demo:** [https://expense-splitter-group-tab-tracker.onrender.com](https://expense-splitter-group-tab-tracker.onrender.com)

---

## ✨ Features

- **Split Flexibility:** Supports equal splits among all or custom subsets of members[cite: 1, 4].
- **Minimal Debt Settlement:** Implements a greedy algorithm (`simplify_debts`) to eliminate redundant circular IOUs and compute the lowest possible number of payment transfers.
- **Settlement Tracking:** Directly record direct peer-to-peer repayments to balance the tab[cite: 1, 4].
- **Spending Analytics:** Live breakdown of total expenditure, expense count, and category distributions[cite: 4, 5].
- **Responsive Mascot UI:** Built with clean custom CSS, mobile responsive card grids, and semantic HTML[cite: 5].

---

## 🛠️ Tech Stack

- **Backend:** Python 3, Flask[cite: 1, 3]
- **WSGI Server:** Gunicorn[cite: 3]
- **Frontend:** Jinja2 templates, HTML5, CSS3[cite: 1, 5]
- **Deployment:** Render

---

## 📁 Repository Structure

```text
├── app.py              # Flask server and web routes
├── tracker.py          # Core logic (Expense, Settlement, GroupTabTracker)
├── requirements.txt    # Production dependencies
├── templates/
│   └── index.html      # Responsive frontend template
└── README.md
```[cite: 1, 3, 4]

---

## 🚀 Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/tnuislostq/Expense-Splitter-Group-Tab-Tracker.git](https://github.com/tnuislostq/Expense-Splitter-Group-Tab-Tracker.git)
   cd Expense-Splitter-Group-Tab-Tracker
