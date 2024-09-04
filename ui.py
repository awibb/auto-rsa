import streamlit as st
import subprocess
import pandas as pd
import os
from streamlit_extras.stylable_container import stylable_container
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

st.set_page_config(
    page_title="auto-rsa-ui",  
    page_icon="🚀",               
    layout="centered",            
    initial_sidebar_state="auto",
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)

# Function to save DataFrame to a CSV file
def save_to_csv(df, file_path):
    try:
        df.to_csv(file_path, index=False)
        print(f"Data saved successfully to {file_path}")
    except Exception as e:
        print(f"Error saving to CSV: {e}")

# Function to load DataFrame from a CSV file
def load_from_csv(file_path):
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
            print(f"Loaded data from {file_path}")
            return df
        except Exception as e:
            print(f"Error loading CSV: {e}")
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
    print(f"Executing {side} {amt}, {tickers}, {brokers}")
    # Load environment variables
    load_dotenv()
    if not os.getenv("SCRIPT_PATH"):
        print("Script Path not found, skipping...")
        return
    script_path = os.environ["SCRIPT_PATH"]

    # Prepare arguments for the subprocess
    args = [side, str(amt), ",".join(tickers), brokers, str(dry)]
    print(f"Arguments: {args}")
    
    # Start the subprocess
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
    while True:
        stdout_line = process.stdout.readline().strip()
        if stdout_line:
            print(stdout_line)  # Print each stdout line to console in real time
            if "Running bot from command line" in stdout_line:
                start_capture = True
                continue
            if start_capture:
                stdout_lines.append(stdout_line)
        
        stderr_line = process.stderr.readline().strip()
        if stderr_line:
            print(f"Error: {stderr_line}")  # Print each stderr line to console in real time
            stderr_lines.append(stderr_line)
        
        if process.poll() is not None and not stdout_line and not stderr_line:
            break

    process.stdout.close()
    process.stderr.close()
    process.wait()

    return stdout_lines, stderr_lines

def run_multiple_commands(commands):
    results = []
    
    # Run multiple processes concurrently using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=len(commands)) as executor:
        # Submit tasks to the thread pool
        futures = [executor.submit(handle_transaction, *command) for command in commands]

        # Collect results as they complete
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as exc:
                print(f'Generated an exception: {exc}')
    
    return results


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
    # st.write("\n".join(stdout_lines))
    # st.write("\n".join(stderr_lines))
    process.wait()
    st.write("Syncing Complete.")

def validate_input(brokers,tickers,side,amt):
    output = []
    if not brokers:
        return [False, "Broker selection is empty, please select your broker(s)."]
    if not tickers:
        return [False, "Ticker(s) is empty please input your ticker(s)"]
    if not amt or 0 >= amt:
        return [False, "Quantity must be an positive Integer"]
    for broker in brokers:
        output.append([True,broker,tickers.split(","),side,amt])
    
    return output

# Main function for Streamlit app
def main():
    load_dotenv()
    with open('./config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)
    
    all_brokers = ["All", "Most", "Day1", "Fennel", "Chase", "Firstrade", "Public", "Robinhood", "Schwab", "TastyTrade", "Tradier", "Webull"]

    

    # Pre-hashing all plain text passwords once
    # Hasher.hash_passwords(config['credentials'])
    
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        config['pre-authorized']
    )
    authenticator.login()


    if st.session_state['authentication_status']:
    # Define file path for persistent storage
        if not os.getenv("OUTPUT_PATH"):
            st.error("Output Path not found, skipping...")
            return
        file_path =  os.environ["OUTPUT_PATH"]
        if 'df_std_output' not in st.session_state:
            st.session_state.df_std_output = load_from_csv(file_path)
            
    
        
        st.write(f'Welcome *{st.session_state["name"]}*')

        # Load existing DataFrame or initialize a new one
        
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
                all_brokers
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
                if not validate[0]:
                    st.warning(validate[1],icon="⚠️")
                if validate[0]:
                    print(validate)
                    commands = []
                    for broker in validate:
                        print("broker: ", broker)
                        print("BROKER 1: ", broker[1])
                        if broker[1] == 'All':
                            print("IN ALL IF")
                            exclude = ["All", "Most", "Day1"]
                            print("all brokers: ", all_brokers)
                            for brk in all_brokers:
                                if brk in exclude:
                                    continue
                                commands.append((broker[3],broker[4],broker[2],brk,dry_mode))
                        else:
                            commands.append((broker[3],broker[4],broker[2],broker[1],dry_mode))
                    print("COMMANDS: ", commands)
                    results = run_multiple_commands(commands)
                    print(results)
                    for stdout, stderr in results:
                        print("STDOUT:", stdout)
                        print("STDERR:", stderr)
            
                   
                    for trans in results:
                        for message in trans:
                            print("STDOUT:", message)
                            df_output = pd.DataFrame(message, columns=['Output'])
                            st.session_state.df_std_output = pd.concat([st.session_state.df_std_output, df_output], ignore_index=True)
                            save_to_csv(st.session_state.df_std_output, file_path)
                    st.info("BUY complete")

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
                if not validate[0]:
                    st.warning(validate[1],icon="⚠️")
                if validate[0]:
                    print(validate)
                    commands = []
                    for broker in validate:
                        print("broker: ", broker)
                        print("BROKER 1: ", broker[1])
                        if broker[1] == 'All':
                            print("IN ALL IF")
                            exclude = ["All", "Most", "Day1"]
                            print("all brokers: ", all_brokers)
                            for brk in all_brokers:
                                if brk in exclude:
                                    continue
                                commands.append((broker[3],broker[4],broker[2],brk,dry_mode))
                        else:
                            commands.append((broker[3],broker[4],broker[2],broker[1],dry_mode))
                    print("COMMANDS: ", commands)
                    results = run_multiple_commands(commands)
                    print(results)
                    for stdout, stderr in results:
                        print("STDOUT:", stdout)
                        print("STDERR:", stderr)
            
                   
                    for trans in results:
                        for message in trans:
                            print("STDOUT:", message)
                            df_output = pd.DataFrame(message, columns=['Output'])
                            st.session_state.df_std_output = pd.concat([st.session_state.df_std_output, df_output], ignore_index=True)
                            save_to_csv(st.session_state.df_std_output, file_path)
                    st.info("SELL complete")

        # Display current DataFrame
        if not st.session_state.df_std_output.empty:
            st.dataframe(st.session_state.df_std_output, use_container_width=True)
        else:
            
            st.error("Error loading CSV: "+ file_path)
            
        if st.button(label="Clear Logs", type="primary"):
            clear_csv(file_path)
        st.image(image='https://i.gyazo.com/620b1e529fe0b4425cbaff3e67776386.png')
        
if __name__ == "__main__":
    main()