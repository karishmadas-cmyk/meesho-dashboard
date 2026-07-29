import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Meesho Losses and Debit Tracking Dashboard",
    page_icon="📦",
    layout="wide"
)

# -----------------------------------------------------------------------------
# CUSTOM CSS
# -----------------------------------------------------------------------------
st.markdown("""
<style>

.kpi-card {
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 20px 12px;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    min-height: 110px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    overflow: hidden;
}

.kpi-value {
    font-size: 26px;
    font-weight: 700;
    color: #d9383a !important;
    line-height: 1.2;
    margin-bottom: 10px;
    white-space: nowrap;
}

.kpi-label {
    font-size: 13px;
    font-weight: 400;
    color: #555555 !important;
    line-height: 1.4;
    white-space: normal;
    word-wrap: break-word;
}

.insight-card {
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 15px;
    height: 100%;
    color: #212529 !important;
    word-wrap: break-word;
}

.insight-card h5,
.insight-card b,
.insight-card li,
.insight-card span,
.insight-card div {
    color: #212529 !important;
}

</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
ALL_MONTHS = [
    "Jan", "Feb", "Mar", "Apr",
    "May", "Jun", "Jul", "Aug",
    "Sep", "Oct", "Nov", "Dec"
]


# -----------------------------------------------------------------------------
# DATA LOADING
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():

    file_path = "Meesho dashboard.xlsx"

    debit_df = pd.read_excel(
        file_path,
        sheet_name="Debit"
    )

    weekly_df = pd.read_excel(
        file_path,
        sheet_name="Weekly file"
    )

    shortage_df = pd.read_excel(
        file_path,
        sheet_name="Shortage"
    )

    # Clean column names
    shortage_df.rename(
        columns={
            "Assigned/ marked ": "Assigned/ marked"
        },
        inplace=True
    )

    # Prepare date columns
    for df in [
        debit_df,
        weekly_df,
        shortage_df
    ]:

        if "Month" in df.columns:

            df["Month"] = pd.to_datetime(
                df["Month"],
                errors="coerce"
            )

            df["Year"] = (
                df["Month"]
                .dt.year
                .astype("Int64")
                .astype(str)
            )

            df["Month_Name"] = (
                df["Month"]
                .dt.strftime("%b")
            )

            df["Month_Year"] = (
                df["Month"]
                .dt.strftime("%b %Y")
            )

            df.sort_values(
                by="Month",
                inplace=True
            )

    return (
        debit_df,
        weekly_df,
        shortage_df
    )


try:

    debit_df, weekly_df, shortage_df = load_data()

except Exception as e:

    st.error(
        f"Please ensure 'Meesho dashboard.xlsx' is in the same folder as app.py. Error: {e}"
    )

    st.stop()


# -----------------------------------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------------------------------
def format_currency(num):

    if num >= 1e7:
        return f"₹ {num / 1e7:.2f} Cr"

    elif num >= 1e5:
        return f"₹ {num / 1e5:.2f} L"

    elif num >= 1e3:
        return f"₹ {num / 1e3:.0f}K"

    else:
        return f"₹ {num:,.0f}"


def format_count(num):

    if num >= 1e3:
        return f"{num / 1e3:.0f}K"

    return str(int(num))


def format_hbar_chart(
    fig,
    x_title="Shipment Count",
    y_title="Location",
    height=320
):

    fig.update_yaxes(
        categoryorder="total ascending",
        title=y_title
    )

    fig.update_xaxes(
        title=x_title
    )

    fig.update_layout(
        margin=dict(
            l=80,
            r=20,
            t=35,
            b=45
        ),
        height=height,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    return fig


def calculate_debit_mom(
    df,
    sel_year,
    sel_month,
    sel_location,
    sel_loss_type
):

    d = df.copy()

    if sel_location != "All":

        d = d[
            d["Location"] == sel_location
        ]

    if sel_loss_type != "All":

        d = d[
            d["Loss Type"] == sel_loss_type
        ]

    monthly = (
        d.groupby("Month")["Total amount"]
        .sum()
        .reset_index()
        .sort_values("Month")
    )

    if monthly.empty:

        return "N/A", "#666666"

    monthly["Year_str"] = (
        monthly["Month"]
        .dt.year
        .astype(str)
    )

    monthly["Month_Name_str"] = (
        monthly["Month"]
        .dt.strftime("%b")
    )

    if sel_month != "All":

        if sel_year != "All":

            target_rows = monthly[
                (monthly["Year_str"] == sel_year)
                &
                (
                    monthly["Month_Name_str"]
                    == sel_month
                )
            ]

        else:

            target_rows = monthly[
                monthly["Month_Name_str"]
                == sel_month
            ]

        if target_rows.empty:

            return "N/A", "#666666"

        target_idx = target_rows.index[-1]

        curr_val = monthly.loc[
            target_idx,
            "Total amount"
        ]

        pos = monthly.index.get_loc(
            target_idx
        )

        if pos > 0:

            prev_val = monthly.iloc[
                pos - 1
            ]["Total amount"]

        else:

            return "N/A", "#666666"

    else:

        if sel_year != "All":

            monthly = monthly[
                monthly["Year_str"]
                == sel_year
            ]

        if len(monthly) < 2:

            return "N/A", "#666666"

        curr_val = monthly.iloc[
            -1
        ]["Total amount"]

        prev_val = monthly.iloc[
            -2
        ]["Total amount"]

    if prev_val == 0:

        return "+100%", "#d9383a"

    pct_change = (
        (curr_val - prev_val)
        / prev_val
    ) * 100

    if pct_change > 0:

        return (
            f"+{pct_change:.1f}%",
            "#d9383a"
        )

    elif pct_change < 0:

        return (
            f"{pct_change:.1f}%",
            "#28a745"
        )

    else:

        return (
            "0.0%",
            "#666666"
        )


# -----------------------------------------------------------------------------
# NAVIGATION
# -----------------------------------------------------------------------------
st.title(
    "📦 Meesho Losses and Debit Tracking Dashboard"
)

page = st.sidebar.radio(
    "Navigation",
    [
        "SHORTAGE VIEW",
        "DEBIT VIEW"
    ]
)


# =============================================================================
# SHORTAGE VIEW
# =============================================================================
if page == "SHORTAGE VIEW":

    st.subheader(
        "Shortage Overview & Analysis"
    )

    # -------------------------------------------------------------------------
    # FILTERS
    # -------------------------------------------------------------------------
    f1, f2, f3, f4 = st.columns(4)

    years = (
        ["All"]
        + sorted(
            list(
                shortage_df["Year"]
                .dropna()
                .unique()
            )
        )
    )

    sel_year = f1.selectbox(
        "Year",
        years,
        index=0
    )

    sel_month = f2.selectbox(
        "Month",
        ["All"] + ALL_MONTHS,
        index=0
    )

    assigned_opts = (
        ["All"]
        + list(
            shortage_df[
                "Assigned/ marked"
            ]
            .dropna()
            .unique()
        )
    )

    sel_assigned = f3.selectbox(
        "Assigned/ marked",
        assigned_opts,
        index=0
    )

    locations = (
        ["All"]
        + list(
            shortage_df[
                "Location"
            ]
            .dropna()
            .unique()
        )
    )

    sel_location = f4.selectbox(
        "Location",
        locations,
        index=0
    )


    # -------------------------------------------------------------------------
    # FILTER DATA
    # -------------------------------------------------------------------------
    filtered_df = shortage_df.copy()

    if sel_year != "All":

        filtered_df = filtered_df[
            filtered_df["Year"]
            == sel_year
        ]

    if sel_month != "All":

        filtered_df = filtered_df[
            filtered_df["Month_Name"]
            == sel_month
        ]

    if sel_assigned != "All":

        filtered_df = filtered_df[
            filtered_df["Assigned/ marked"]
            == sel_assigned
        ]

    if sel_location != "All":

        filtered_df = filtered_df[
            filtered_df["Location"]
            == sel_location
        ]


    # -------------------------------------------------------------------------
    # SHORTAGE KPIs + INSIGHTS
    # -------------------------------------------------------------------------
    c1, c2, c3 = st.columns(
        [1, 1, 1.5]
    )

    total_short_shipments = len(
        filtered_df
    )

    total_shortage_amount = (
        filtered_df[
            "Total Amount"
        ].sum()
    )

    top_cat = (
        filtered_df[
            "Assigned/ marked"
        ].mode()[0]
        if not filtered_df.empty
        else "N/A"
    )

    top_loc = (
        filtered_df[
            "Location"
        ].mode()[0]
        if not filtered_df.empty
        else "N/A"
    )

    top_reason = (
        filtered_df[
            "Shorage type"
        ].mode()[0]
        if not filtered_df.empty
        else "N/A"
    )

    peak_month = (
        filtered_df
        .groupby(
            "Month_Year"
        )[
            "Total Amount"
        ]
        .sum()
        .idxmax()
        if not filtered_df.empty
        else "N/A"
    )


    with c1:

        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-value">
                    {format_count(total_short_shipments)}
                </div>
                <div class="kpi-label">
                    Short Shipments
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


    with c2:

        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-value">
                    {format_currency(total_shortage_amount)}
                </div>
                <div class="kpi-label">
                    Shortage Amount
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


    with c3:

        st.markdown(
            f"""
            <div class="insight-card">

                <h5 style="margin-top:0px; margin-bottom:8px;">
                    Shortage Insights
                </h5>

                <ul style="
                    margin-top:0px;
                    margin-bottom:0px;
                    padding-left:20px;
                    font-size:14px;
                    line-height:1.8;
                ">

                    <li>
                        <b>Highest category:</b>
                        {top_cat}
                    </li>

                    <li>
                        <b>Total shortage cases:</b>
                        {total_short_shipments:,}
                    </li>

                    <li>
                        <b>Total shortage loss value:</b>
                        ₹{total_shortage_amount:,.0f}
                    </li>

                    <li>
                        <b>Highest shortage location:</b>
                        {top_loc}
                    </li>

                    <li>
                        <b>Major shortage reason:</b>
                        {top_reason}
                    </li>

                    <li>
                        <b>Shortage peak month:</b>
                        {peak_month}
                    </li>

                </ul>

            </div>
            """,
            unsafe_allow_html=True
        )


    st.markdown(
        "<br>",
        unsafe_allow_html=True
    )


    # -------------------------------------------------------------------------
    # SHORTAGE CHARTS
    # -------------------------------------------------------------------------
    col_left, col_right = st.columns(2)


    with col_left:

        st.markdown(
            "##### Top 5 Locations Creating Shortages"
        )

        loc_df = (
            filtered_df
            .groupby("Location")
            .size()
            .reset_index(
                name="Shipment Count"
            )
            .sort_values(
                by="Shipment Count",
                ascending=False
            )
            .head(5)
        )

        fig_loc = px.bar(
            loc_df,
            x="Shipment Count",
            y="Location",
            orientation="h"
        )

        fig_loc.update_traces(
            name="Shipments"
        )

        format_hbar_chart(
            fig_loc,
            "Shipment Count",
            "Location",
            320
        )

        st.plotly_chart(
            fig_loc,
            use_container_width=True
        )


    with col_right:

        st.markdown(
            "##### Shortage Trend"
        )

        trend_df = (
            filtered_df
            .groupby("Month")[
                "Total Amount"
            ]
            .sum()
            .reset_index()
            .sort_values("Month")
        )

        fig_trend = px.line(
            trend_df,
            x="Month",
            y="Total Amount",
            markers=True
        )

        fig_trend.update_traces(
            name="Shortage Loss Amount"
        )

        fig_trend.update_xaxes(
            dtick="M2",
            tickformat="%b %Y",
            title="Month"
        )

        fig_trend.update_yaxes(
            title="Loss Amount (₹)"
        )

        fig_trend.update_layout(
            margin=dict(
                l=70,
                r=20,
                t=35,
                b=45
            ),
            height=320,
            showlegend=True
        )

        st.plotly_chart(
            fig_trend,
            use_container_width=True
        )


    # -------------------------------------------------------------------------
    # BOTTOM SHORTAGE SECTION
    # -------------------------------------------------------------------------
    col_bottom_left, col_bottom_right = st.columns(
        [1, 1.2]
    )


    with col_bottom_left:

        st.markdown(
            "##### Top 5 Users Creating Shortages"
        )

        user_df = (
            filtered_df
            .groupby("Assigned user")
            .size()
            .reset_index(
                name="Shipment Count"
            )
            .sort_values(
                by="Shipment Count",
                ascending=False
            )
            .head(5)
        )

        fig_user = px.bar(
            user_df,
            x="Shipment Count",
            y="Assigned user",
            orientation="h"
        )

        fig_user.update_traces(
            name="Shipments"
        )

        format_hbar_chart(
            fig_user,
            "Shipment Count",
            "Assigned User",
            300
        )

        st.plotly_chart(
            fig_user,
            use_container_width=True
        )


    with col_bottom_right:

        st.markdown(
            "##### Detail Summary Table"
        )

        table_df = (
            filtered_df
            .groupby(
                [
                    "Assigned user",
                    "Location"
                ]
            )
            .agg(
                Count_of_AWB=(
                    "AWB",
                    "count"
                ),
                Sum_of_Total_Amount=(
                    "Total Amount",
                    "sum"
                )
            )
            .reset_index()
            .sort_values(
                by="Sum_of_Total_Amount",
                ascending=False
            )
        )

        st.dataframe(
            table_df,
            column_config={
                "Assigned user":
                    "Assigned user",

                "Location":
                    "Location",

                "Count_of_AWB":
                    "Count of AWB",

                "Sum_of_Total_Amount":
                    st.column_config.NumberColumn(
                        "Sum of Total Amount",
                        format="₹ %d"
                    )
            },
            hide_index=True,
            use_container_width=True,
            height=300
        )


# =============================================================================
# DEBIT VIEW
# =============================================================================
elif page == "DEBIT VIEW":

    st.subheader(
        "Debit Overview & Monthly Trend"
    )


    # -------------------------------------------------------------------------
    # FILTERS
    # -------------------------------------------------------------------------
    f1, f2, f3, f4 = st.columns(4)

    years = (
        ["All"]
        + sorted(
            list(
                debit_df[
                    "Year"
                ]
                .dropna()
                .unique()
            )
        )
    )

    sel_year = f1.selectbox(
        "Year",
        years,
        index=0
    )

    sel_month = f2.selectbox(
        "Month",
        ["All"] + ALL_MONTHS,
        index=0
    )

    locations = (
        ["All"]
        + list(
            debit_df[
                "Location"
            ]
            .dropna()
            .unique()
        )
    )

    sel_location = f3.selectbox(
        "Location",
        locations,
        index=0
    )

    loss_types = (
        ["All"]
        + list(
            debit_df[
                "Loss Type"
            ]
            .dropna()
            .unique()
        )
    )

    sel_loss_type = f4.selectbox(
        "Loss Type",
        loss_types,
        index=0
    )


    # -------------------------------------------------------------------------
    # FILTER DATA
    # -------------------------------------------------------------------------
    filtered_debit = debit_df.copy()

    filtered_weekly = weekly_df.copy()


    if sel_year != "All":

        filtered_debit = filtered_debit[
            filtered_debit["Year"]
            == sel_year
        ]

        filtered_weekly = filtered_weekly[
            filtered_weekly["Year"]
            == sel_year
        ]


    if sel_month != "All":

        filtered_debit = filtered_debit[
            filtered_debit["Month_Name"]
            == sel_month
        ]

        filtered_weekly = filtered_weekly[
            filtered_weekly["Month_Name"]
            == sel_month
        ]


    if sel_location != "All":

        filtered_debit = filtered_debit[
            filtered_debit["Location"]
            == sel_location
        ]

        filtered_weekly = filtered_weekly[
            filtered_weekly["Location"]
            == sel_location
        ]


    if sel_loss_type != "All":

        filtered_debit = filtered_debit[
            filtered_debit["Loss Type"]
            == sel_loss_type
        ]


    # -------------------------------------------------------------------------
    # KPI CALCULATIONS
    # -------------------------------------------------------------------------
    total_shipment_count = len(
        filtered_debit
    )

    overall_debit_amount = (
        filtered_debit[
            "Total amount"
        ].sum()
    )

    weekly_debit_amount = (
        filtered_weekly[
            "Value"
        ].sum()
    )

    # NEW:
    # Weekly Debit AWB Count
    weekly_debit_awb_count = (
        filtered_weekly[
            "AWB"
        ]
        .nunique()
    )

    mom_value, mom_color = calculate_debit_mom(
        debit_df,
        sel_year,
        sel_month,
        sel_location,
        sel_loss_type
    )


    # -------------------------------------------------------------------------
    # KPI CARDS - 5 CARDS
    # -------------------------------------------------------------------------
    c1, c2, c3, c4, c5 = st.columns(5)


    # KPI 1
    with c1:

        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-value">
                    {format_count(total_shipment_count)}
                </div>

                <div class="kpi-label">
                    Shipment Count (Overall Debit)
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


    # KPI 2
    with c2:

        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-value">
                    {format_currency(overall_debit_amount)}
                </div>

                <div class="kpi-label">
                    Overall Debit
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


    # KPI 3
    with c3:

        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-value">
                    {format_currency(weekly_debit_amount)}
                </div>

                <div class="kpi-label">
                    Weekly Debit
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


    # KPI 4 - NEW
    with c4:

        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-value">
                    {format_count(weekly_debit_awb_count)}
                </div>

                <div class="kpi-label">
                    Weekly Debit AWB Count
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


    # KPI 5 - MOM
    with c5:

        st.markdown(
            f"""
            <div class="kpi-card">

                <div
                    class="kpi-value"
                    style="color: {mom_color} !important;"
                >
                    {mom_value}
                </div>

                <div class="kpi-label">
                    Debit MoM (vs Last Month)
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


    st.markdown(
        "<br>",
        unsafe_allow_html=True
    )


    # -------------------------------------------------------------------------
    # TREND CHARTS
    # -------------------------------------------------------------------------
    col_l1, col_l2 = st.columns(2)


    with col_l1:

        st.markdown(
            "##### WEEKLY DEBIT - MONTHLY TREND"
        )

        w_trend = (
            filtered_weekly
            .groupby("Month")[
                "Value"
            ]
            .sum()
            .reset_index()
            .sort_values("Month")
        )

        fig_w = px.line(
            w_trend,
            x="Month",
            y="Value",
            markers=True
        )

        fig_w.update_traces(
            name="Weekly Debit Amount"
        )

        fig_w.update_xaxes(
            dtick="M2",
            tickformat="%b %Y",
            title="Month"
        )

        fig_w.update_yaxes(
            title="Debit Amount (₹)"
        )

        fig_w.update_layout(
            margin=dict(
                l=70,
                r=20,
                t=35,
                b=45
            ),
            height=320,
            showlegend=True
        )

        st.plotly_chart(
            fig_w,
            use_container_width=True
        )


    with col_l2:

        st.markdown(
            "##### OVERALL DEBIT - MONTHLY TREND"
        )

        o_trend = (
            filtered_debit
            .groupby("Month")[
                "Total amount"
            ]
            .sum()
            .reset_index()
            .sort_values("Month")
        )

        fig_o = px.line(
            o_trend,
            x="Month",
            y="Total amount",
            markers=True
        )

        fig_o.update_traces(
            name="Overall Debit Amount"
        )

        fig_o.update_xaxes(
            dtick="M2",
            tickformat="%b %Y",
            title="Month"
        )

        fig_o.update_yaxes(
            title="Debit Amount (₹)"
        )

        fig_o.update_layout(
            margin=dict(
                l=70,
                r=20,
                t=35,
                b=45
            ),
            height=320,
            showlegend=True
        )

        st.plotly_chart(
            fig_o,
            use_container_width=True
        )


    # -------------------------------------------------------------------------
    # TOP 5 MONTHLY CONTRIBUTORS
    # -------------------------------------------------------------------------
    st.markdown(
        "<br>",
        unsafe_allow_html=True
    )

    st.markdown(
        "##### TOP 5 MONTHLY CONTRIBUTORS"
    )


    if not filtered_debit.empty:

        top_5_locs = (
            filtered_debit
            .groupby("Location")[
                "Total amount"
            ]
            .sum()
            .nlargest(5)
            .index
            .tolist()
        )

        df_top5 = filtered_debit[
            filtered_debit[
                "Location"
            ].isin(
                top_5_locs
            )
        ]

        df_top5_grouped = (
            df_top5
            .groupby(
                [
                    "Month",
                    "Location"
                ]
            )[
                "Total amount"
            ]
            .sum()
            .reset_index()
            .sort_values("Month")
        )

        fig_top5 = px.bar(
            df_top5_grouped,
            x="Month",
            y="Total amount",
            color="Location",
            barmode="stack"
        )

        fig_top5.update_xaxes(
            dtick="M2",
            tickformat="%b %Y",
            title="Month"
        )

        fig_top5.update_yaxes(
            title="Total Amount (₹)"
        )

        fig_top5.update_layout(
            margin=dict(
                l=70,
                r=20,
                t=35,
                b=45
            ),
            height=320,
            showlegend=True
        )

        st.plotly_chart(
            fig_top5,
            use_container_width=True
        )


    # -------------------------------------------------------------------------
    # TOP 5 WEEKLY DEBIT CONTRIBUTORS
    # -------------------------------------------------------------------------
    st.markdown(
        "<br>",
        unsafe_allow_html=True
    )

    st.markdown(
        "##### TOP 5 WEEKLY DEBIT CONTRIBUTORS"
    )


    if not filtered_weekly.empty:

        top_5_weekly_locs = (
            filtered_weekly
            .groupby("Location")[
                "Value"
            ]
            .sum()
            .nlargest(5)
            .index
            .tolist()
        )

        df_weekly_top5 = filtered_weekly[
            filtered_weekly[
                "Location"
            ].isin(
                top_5_weekly_locs
            )
        ].copy()

        df_weekly_top5_grouped = (
            df_weekly_top5
            .groupby(
                [
                    "Month",
                    "Location"
                ]
            )[
                "Value"
            ]
            .sum()
            .reset_index()
            .sort_values("Month")
        )

        fig_weekly_top5 = px.bar(
            df_weekly_top5_grouped,
            x="Month",
            y="Value",
            color="Location",
            barmode="stack"
        )

        fig_weekly_top5.update_xaxes(
            dtick="M2",
            tickformat="%b %Y",
            title="Month"
        )

        fig_weekly_top5.update_yaxes(
            title="Weekly Debit Amount (₹)"
        )

        fig_weekly_top5.update_layout(
            margin=dict(
                l=70,
                r=20,
                t=35,
                b=45
            ),
            height=320,
            showlegend=True
        )

        st.plotly_chart(
            fig_weekly_top5,
            use_container_width=True
        )

    else:

        st.info(
            "No weekly debit data available for the selected filters."
        )


    # -------------------------------------------------------------------------
    # LOSS CATEGORY + KEY INSIGHTS
    # -------------------------------------------------------------------------
    st.markdown(
        "<br>",
        unsafe_allow_html=True
    )

    col_b1, col_b2 = st.columns(2)


    with col_b1:

        st.markdown(
            "##### OVERALL LOSS CATEGORY OVERVIEW"
        )

        loss_cat = (
            filtered_debit
            .groupby("Loss Type")[
                "Total amount"
            ]
            .sum()
            .reset_index()
        )

        fig_donut = px.pie(
            loss_cat,
            values="Total amount",
            names="Loss Type",
            hole=0.5
        )

        fig_donut.update_layout(
            margin=dict(
                l=20,
                r=20,
                t=30,
                b=30
            ),
            height=320,
            showlegend=True
        )

        st.plotly_chart(
            fig_donut,
            use_container_width=True
        )


    with col_b2:

        top_loss_month = (
            filtered_debit
            .groupby(
                "Month_Year"
            )[
                "Total amount"
            ]
            .sum()
            .idxmax()
            if not filtered_debit.empty
            else "N/A"
        )

        top_loss_loc = (
            filtered_debit[
                "Location"
            ].mode()[0]
            if not filtered_debit.empty
            else "N/A"
        )


        st.markdown(
            f"""
            <div class="insight-card">

                <h5 style="margin-top:0px; margin-bottom:8px;">
                    Key Insights
                </h5>

                <ul style="
                    margin-top:0px;
                    margin-bottom:0px;
                    padding-left:20px;
                    font-size:14px;
                    line-height:1.8;
                ">

                    <li>
                        <b>Highest loss month:</b>
                        {top_loss_month}
                    </li>

                    <li>
                        <b>Highest loss location:</b>
                        {top_loss_loc}
                    </li>

                    <li>
                        <b>Total shipments impacted:</b>
                        {total_shipment_count:,}
                    </li>

                    <li>
                        <b>Total loss value:</b>
                        ₹{overall_debit_amount:,.0f}
                    </li>

                </ul>

            </div>
            """,
            unsafe_allow_html=True
        )
