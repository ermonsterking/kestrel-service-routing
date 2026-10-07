import requests
import streamlit as st


API_URL = "http://127.0.0.1:8000/route"


# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="Kestrel Home — Service Router",
    page_icon="🔧",
    layout="centered",
)


# =============================================================================
# HEADER
# =============================================================================

st.title("Kestrel Home")
st.subheader("AI Service Request Routing")

st.write(
    "Enter a customer's request and the available request metadata. "
    "The system first checks whether the request is safe to route automatically. "
    "Clear requests are then assigned to the appropriate service team."
)


# =============================================================================
# CUSTOMER REQUEST
# =============================================================================

request_text = st.text_area(
    "Customer request",
    placeholder=(
        "Example: My water purifier is leaking water from the bottom "
        "and is not working"
    ),
    height=130,
)


# =============================================================================
# REQUEST METADATA
# =============================================================================

col1, col2 = st.columns(2)

with col1:

    product_family = st.selectbox(
        "Product family",
        [
            "Water Purifier",
            "Air Fryer",
            "Mixer Grinder",
            "Induction Cooktop",
            "Room Heater",
            "Ceiling Fan",
            "Robot Vacuum",
        ],
    )

    warranty_status = st.selectbox(
        "Warranty status",
        [
            "in_warranty",
            "out_of_warranty",
            "shield",
        ],
    )


with col2:

    channel = st.selectbox(
        "Channel",
        [
            "chat",
            "whatsapp",
            "ivr",
            "email",
        ],
    )

    source = st.selectbox(
        "Source",
        [
            "crm",
            "legacy_zoho",
        ],
    )


# =============================================================================
# ROUTING
# =============================================================================

if st.button("Route Request", type="primary"):

    if not request_text.strip():

        st.warning(
            "Please enter the customer's request."
        )

    else:

        payload = {
            "request_text": request_text,
            "product_family": product_family,
            "warranty_status": warranty_status,
            "channel": channel,
            "source": source,
        }

        try:

            response = requests.post(
                API_URL,
                json=payload,
                timeout=10,
            )

            response.raise_for_status()

            result = response.json()

            status = result.get("status")


            # =================================================================
            # ROUTABLE
            # =================================================================

            if status == "ROUTABLE":

                st.success(
                    "Request approved for automatic routing"
                )

                st.markdown("### 🎯 Assigned Team")

                st.info(
                    f"**{result['predicted_team']}**"
                )

                st.markdown("### Why this team?")

                st.write(
                    result.get(
                        "reason",
                        "The request was classified as routable."
                    )
                )


            # =================================================================
            # NEEDS CLARIFICATION
            # =================================================================

            elif status == "NEEDS_CLARIFICATION":

                st.warning(
                    "Additional information is required"
                )

                st.markdown("### 💬 Clarification Question")

                st.info(
                    result.get(
                        "clarification_question",
                        "What specific issue are you experiencing?"
                    )
                )

                st.caption(
                    "The system intentionally avoids forcing an uncertain "
                    "request into a service queue."
                )


            # =================================================================
            # MULTI INTENT
            # =================================================================

            elif status == "MULTI_INTENT":

                st.warning(
                    "Multiple issues detected"
                )

                st.markdown("### 💬 Clarification Required")

                st.info(
                    result.get(
                        "clarification_question",
                        "Which issue should be handled first?"
                    )
                )

                st.caption(
                    "The request should be separated or prioritized "
                    "before assigning a service team."
                )


            # =================================================================
            # DATA CONFLICT
            # =================================================================

            elif status == "DATA_CONFLICT":

                st.error(
                    "Request metadata conflict detected"
                )

                st.markdown("### ⚠️ Review Required")

                st.write(
                    result.get(
                        "reason",
                        "The request text and product metadata "
                        "appear inconsistent."
                    )
                )

                st.caption(
                    "Please verify the product information before "
                    "routing the request."
                )


            # =================================================================
            # UNKNOWN STATUS
            # =================================================================

            else:

                st.error(
                    "The routing service returned an unexpected status."
                )

                st.json(result)


        # =====================================================================
        # CONNECTION ERROR
        # =====================================================================

        except requests.exceptions.ConnectionError:

            st.error(
                "Routing service is unavailable. "
                "Please start the FastAPI service first."
            )


        # =====================================================================
        # REQUEST ERROR
        # =====================================================================

        except requests.exceptions.RequestException as exc:

            st.error(
                f"Routing request failed: {exc}"
            )


# =============================================================================
# FOOTER
# =============================================================================

st.divider()

st.caption(
    "Kestrel Home • Quality-gated service routing • "
    "Requests that are ambiguous or inconsistent are not force-routed."
)
