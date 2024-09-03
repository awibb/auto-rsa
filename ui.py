import streamlit as st
import subprocess
import pandas as pd
import os
from streamlit_extras.stylable_container import stylable_container
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from dotenv import load_dotenv

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
def clear_csv(file_path):
    try:
        # Create an empty DataFrame
        empty_df = pd.DataFrame()

        # Save the empty DataFrame to the CSV to overwrite existing data
        save_to_csv(empty_df, file_path)

        # Update the session state DataFrame
        st.session_state.df_std_output = empty_df

        st.success("Logs cleared successfully.")
    except Exception as e:
        st.error(f"Error clearing logs: {e}")


# Function to handle "Buy" button logic
def handle_transaction(side,amt,tickers,brokers,dry):
    print(f"Executing {side} command")
    
    # Load environment variables
    load_dotenv()
    if not os.getenv("SCRIPT_PATH"):
        print("Script Path not found, skipping...")
        return
    script_path = os.environ["SCRIPT_PATH"]

    # Prepare arguments for the subprocess
    args = [side, amt,",".join(tickers), ",".join(brokers),dry]
    print(f"Arguments: {args}")
    # x = ["python", script_path] + args,
    # print(x)

    process = subprocess.Popen(
        ["python", script_path] + args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1  # Line-buffered output
    )

    stdout_lines = []
    stderr_lines = []

    start_capture = False

    # Collect and filter output in real-time
    for line in iter(process.stdout.readline, ''):
        line = line.strip()
        if line:
            print(line)  # Print output to the console
            stdout_lines.append(line)
            
            # Start capturing after a specific message
            if "Running bot from command line" in line:
                start_capture = True
                continue
            if start_capture:
                stdout_lines.append(line)
    
    for line in iter(process.stderr.readline, ''):
        line = line.strip()
        if line:
            print(f"Error: {line}")  # Print errors to the console
            stderr_lines.append(line)

    # Ensure all output is captured and close the streams
    process.stdout.close()
    process.stderr.close()
    process.wait()

    return stdout_lines, stderr_lines


def handle_sync():
    st.write("Syncing requirements..")
    if not os.getenv("REQUIREMENTS_PATH"):
        st.error("Requirements path not found, skipping...")
        return None
    # Path to requirements.txt
    requirements_path =  os.environ["REQUIREMENTS_PATH"]
    
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
    st.write("\n".join(stdout_lines))
    st.write("\n".join(stderr_lines))
    process.wait()
    st.write("Syncing Complete.")

def validate_input(brokers,tickers,side,amt):
    if not brokers:
        return [False, "Broker selection is empty, please select your broker(s)."]
    if not tickers:
        return [False, "Ticker(s) is empty please input your ticker(s)"]
    if not amt or 0 >= amt:
        return [False, "Quantity must be an positive Integer"]
    return [True, brokers, tickers.split(","),side,amt]

# Main function for Streamlit app
def main():
    # Define file path for persistent storage
    load_dotenv()
    if not os.getenv("OUTPUT_PATH"):
        st.error("Output Path not found, skipping...")
        return
    file_path =  os.environ["OUTPUT_PATH"]
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
        
        st.write(f'Welcome *{st.session_state["name"]}*')

        # Load existing DataFrame or initialize a new one
        if 'df_std_output' not in st.session_state:
            st.session_state.df_std_output = load_from_csv(file_path)
        
        # Sidebar elements
        with st.sidebar:
            # Create columns for side-by-side buttons
            sync_coll, logout_col = st.columns([1, 1])
            
            # Sync button
            with sync_coll:
                if st.button("Sync", use_container_width=True):
                    handle_sync()
            
            # Logout button
            with logout_col:
                if st.button("Logout", use_container_width=True):
                    authenticator.authentication_controller.logout()
                    authenticator.cookie_controller.delete_cookie()
            
            # Broker and Ticker inputs
            options = st.multiselect(
                "Select broker(s)",
                ["All", "Most", "Day1", "Fennel", "Chase", "Fidelity", "FirstTrade", "Public", "Robinhood", "Schwab", "TastyTrade", "Tornado", "Tradier", "Vanguard", "Webull"],
            )
            tickers = st.text_input("Ticker(s)")
            quantity = st.number_input("Quantity", step=1, value=1, help='The number of shares you want to buy/sell.')
            dry_mode = st.toggle("Dry Mode")

            # Create columns for side-by-side buttons
            buy_col, sell_col = st.columns([1, 1])

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
            with buy_col:
                with stylable_container(
                    "green",
                    css_styles=button_style
                ):
                    buy_btn = st.button("Buy", key="buy_btn")
                    # if buy_btn:
                    #     output, errors = handle_transaction()
                    #     df_output = pd.DataFrame(output, columns=['Output'])
                    #     df_err = pd.DataFrame(errors, columns=['Error'])
                    #     st.session_state.df_std_output = pd.concat([st.session_state.df_std_output, df_output, df_err], ignore_index=True)
                    #     save_to_csv(st.session_state.df_std_output, file_path)
            if buy_btn:
                print("Brokers: ", options)
                print("Tickers: ", tickers)
                validate = validate_input(options,tickers,"BUY",quantity)
                print(validate)
                if not validate[0]:
                    st.warning(validate[1],icon="⚠️")
                if validate[0]:
                    handle_transaction(validate[3],validate[4],validate[2],validate[1],dry_mode)
                    st.info("buy")

            with sell_col:
                with stylable_container(
                    "red",
                    css_styles=sell_button_style
                ):
                    sell_btn = st.button("Sell", key="sell_btn")
            if sell_btn:
                print("Brokers: ", options)
                print("Tickers: ", tickers)
                validate = validate_input(options,tickers,"SELL",quantity)
                print(validate)
                if not validate[0]:
                    st.warning(validate[1],icon="⚠️")
                if validate[0]:
                    st.info("sell")

        # Display current DataFrame
        if not st.session_state.df_std_output.empty:
            st.dataframe(st.session_state.df_std_output, use_container_width=True)
            
            if st.button(label="Clear Logs", type="primary"):
                clear_csv(file_path)
        
if __name__ == "__main__":
    main()