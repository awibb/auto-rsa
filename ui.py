import streamlit as st
import subprocess
import pandas as pd
import os
from streamlit_extras.stylable_container import stylable_container
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

# Define file path for persistent storage
file_path = 'C:/Users/Drew-PC/auto-rsa/auto-rsa/output.csv'

# Function to save DataFrame to a CSV file
def save_to_csv(df, file_path):
    try:
        df.to_csv(file_path, index=False)
        st.write(f"Data saved successfully to {file_path}")
    except Exception as e:
        st.error(f"Error saving to CSV: {e}")

# Function to load DataFrame from a CSV file
def load_from_csv(file_path):
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
            # st.write(f"Loaded data from {file_path}")
            return df
        except Exception as e:
            st.error(f"Error loading CSV: {e}")
            return pd.DataFrame()
    else:
        st.write(f"No CSV file found at {file_path}. Starting with an empty DataFrame.")
        return pd.DataFrame()

# Function to handle "Buy" button logic
def handle_buy():
    st.write("Executing buy command")
    # script_path = "C:/Users/Drew-PC/auto-rsa/auto-rsa/autoRSA.py"
    # args = ["holdings", "tastytrade"]

    # process = subprocess.Popen(
    #     ["python", script_path] + args,
    #     stdout=subprocess.PIPE,
    #     stderr=subprocess.PIPE,
    #     text=True
    # )

    # stdout_lines = []
    # stderr_lines = []

    # start_capture = False

    # # Collect and filter output in real time
    # for line in iter(process.stdout.readline, ''):
    #     line = line.strip()
    #     if line:
    #         if "Running bot from command line" in line:
    #             start_capture = True
    #             continue
    #         if start_capture:
    #             stdout_lines.append(line)
    
    # for line in iter(process.stderr.readline, ''):
    #     line = line.strip()
    #     if line:
    #         stderr_lines.append(line)

    # # Ensure all output is captured and close the streams
    # process.stdout.close()
    # process.stderr.close()
    # process.wait()

    # return stdout_lines, stderr_lines

def handle_sync():
    st.write("Syncing requirements..")

    # Path to requirements.txt
    requirements_path = "C:/Users/Drew-PC/auto-rsa/auto-rsa/requirements.txt"
    
    # Run pip install -r requirements.txt
    process = subprocess.Popen(
        ["pip", "install", "-r", requirements_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout_lines = []
    stderr_lines = []

    # Capture output and errors
    for line in iter(process.stdout.readline, ''):
        line = line.strip()
        if line:
            stdout_lines.append(line)
    
    for line in iter(process.stderr.readline, ''):
        line = line.strip()
        if line:
            stderr_lines.append(line)

    # Ensure all output is captured and close the streams
    process.stdout.close()
    process.stderr.close()
    print(stdout_lines)
    print(stderr_lines)
    process.wait()
    st.write("Syncing Complete.")


def validate_input(brokers,tickers):
    if not brokers:
        return [False, "Broker selection is empty, please select your broker(s)."]
    if not tickers:
        return [False, "Ticker(s) is empty please input your ticker(s)"]
    tickers = tickers.split(",")
    return [True, "", tickers]


# Main function for Streamlit app
def main():
    with open('./config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)

    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        config['pre-authorized']
    )
    authenticator.login()

    if st.session_state['authentication_status']:
        authenticator.logout()
        st.write(f'Welcome *{st.session_state["name"]}*')

        # Load existing DataFrame or initialize a new one
        if 'df_std_output' not in st.session_state:
            st.session_state.df_std_output = load_from_csv(file_path)

        # Sidebar elements
        sync_button = st.sidebar.button(label="Sync", on_click=handle_sync)
        options = st.sidebar.multiselect(
            "Select broker(s)",
            ["All", "Most", "Day1", "Fennel", "Chase", "Fidelity", "FirstTrade", "Public", "Robinhood", "Schwab", "TastyTrade", "Tornado", "Tradier", "Vanguard", "Webull"],
        )
        tickers = st.sidebar.text_input("Ticker(s)")
        quantity = st.sidebar.number_input("Quantity", step=1, value=1, help='The number of shares you want to buy/sell.')
        dry_mode = st.sidebar.checkbox("Dry Mode")

        # Create columns for side-by-side buttons
        col1, col2 = st.sidebar.columns([1, 1])

        # Button styles
        button_style = """
        button {
            background-color: #00FF00;
            color: black;
            margin: 0;
            padding: 0.5rem 1rem;
            width: 100%;
        }
        """

        sell_button_style = """
        button {
            background-color: #FF0000;
            color: white;
            margin: 0;
            padding: 0.5rem 1rem;
            width: 100%;
        }
        """

        # Display buttons in columns
        with col1:
            with stylable_container(
                "green",
                css_styles=button_style
            ):
                buy_btn = st.button("Buy", key="buy_btn")
                # if buy_btn:
                #     output, errors = handle_buy()
                #     df_output = pd.DataFrame(output, columns=['Output'])
                #     df_err = pd.DataFrame(errors, columns=['Error'])
                #     st.session_state.df_std_output = pd.concat([st.session_state.df_std_output, df_output, df_err], ignore_index=True)
                #     save_to_csv(st.session_state.df_std_output, file_path)
                if buy_btn:
                    print("Brokers: ", options)
                    print("Tickers: ", tickers)
                    validate = validate_input(options,tickers)
                    print(validate)
                    if not validate[0]:
                        st.sidebar.warning(validate[1])
                    if validate[0]:
                         st.sidebar.info("buy")

        with col2:
            with stylable_container(
                "red",
                css_styles=sell_button_style
            ):
                sell_btn = st.button("Sell", key="sell_btn")
                if sell_btn:
                    print("Brokers: ", options)
                    print("Tickers: ", tickers)
                    validate = validate_input(options,tickers)
                    print(validate)
                    if not validate[0]:
                        st.sidebar.warning(validate[1])
                    if validate[0]:
                         st.sidebar.info("sell")

        # Display current DataFrame
        if not st.session_state.df_std_output.empty:
            st.dataframe(st.session_state.df_std_output, width=1000)
        

if __name__ == "__main__":
    main()
