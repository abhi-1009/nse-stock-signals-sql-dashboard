import pandas as pd
import plotly.express as px
import streamlit as st

import db
import queries
import theme

theme.setup("SQL Playground", "🧪")
theme.header("SQL Playground", "Run the project's queries, or write your own (read-only)")
theme.how_to_read(
    "1. Pick a task to load its query, or choose *Write my own*.\n"
    "2. Edit the SQL if you like and press **Run query**.\n"
    "3. Only a single `SELECT` (or `WITH ... SELECT`) is accepted; results are capped at 1,000 rows.\n"
    "4. Write the `signal` column with backticks: `` `signal` ``.")

CUSTOM = "✏️ Write my own"
choice = st.selectbox("Choose a task", [CUSTOM] + list(queries.PLAYGROUND.keys()))
if choice == CUSTOM:
    desc, default_sql = "Type any SELECT query against the tables listed below.", "SELECT * FROM stock_summary"
else:
    desc, default_sql = queries.PLAYGROUND[choice]
st.caption(desc)

# widget key changes with the task so the editor reloads the selected query
sql = st.text_area("SQL", value=default_sql, height=300, key=f"sql_{choice}")
with st.expander("Tables and columns"):
    st.markdown(queries.SCHEMA_HELP)

if st.button("▶ Run query", type="primary"):
    ok, msg, cleaned = db.validate_readonly(sql)
    if not ok:
        st.error(msg)
    else:
        try:
            with st.spinner("Running..."):
                df, truncated = db.run_readonly(cleaned)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Query failed: {exc}")
        else:
            st.success(f"{len(df):,} row(s) × {len(df.columns)} column(s)")
            if truncated:
                st.warning("Result truncated to the first 1,000 rows.")
            st.dataframe(df, width="stretch", hide_index=True)
            st.download_button("⬇ Download CSV", df.to_csv(index=False).encode(), "query_result.csv", "text/csv")

            # one-click chart when the shape allows it
            num = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
            first = df.columns[0] if len(df.columns) else None
            if first is not None and num and len(df) > 1 and first not in num:
                x = df[first]
                is_date = False
                try:
                    x = pd.to_datetime(x)
                    is_date = True
                except Exception:  # noqa: BLE001
                    pass
                fig = (px.line(df.assign(**{first: x}), x=first, y=num[:4]) if is_date
                       else px.bar(df, x=first, y=num[:3], barmode="group"))
                theme.style_fig(fig, "Quick chart of the result", "", "", height=380)
                st.plotly_chart(fig, width="stretch")
                theme.takeaway("Auto-generated from the first column and the numeric columns; "
                               "rename columns in your SELECT to make it clearer.")
