import pandas as pd
import re

def main():
    file_path = "formato_investigacion_maría_elisa_padilla_fixed.csv"
    print(f"Reading file: {file_path}")
    
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    # Function to remove polarity string
    def clean_text(text):
        if not isinstance(text, str):
            return text
        # Regex to remove " (polaridad: 0.00)" including the leading space
        cleaned = re.sub(r'\s\(polaridad: -?\d+\.\d+\)', '', text)
        return cleaned

    # Apply cleaning to 'Explicación' column
    print("Removing polarity scores...")
    df['Explicación'] = df['Explicación'].apply(clean_text)

    # Save the updated file
    output_path = "formato_investigacion_maría_elisa_padilla_final.csv"
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    # Also overwrite the fixed one just in case
    df.to_csv(file_path, index=False, encoding='utf-8-sig')
    
    print(f"✅ Cleaned file saved to: {output_path}")
    
    # Verify one example
    x_comments = df[df['Red Social'] == 'X (Twitter)']
    if not x_comments.empty:
        print("Example cleaned explanation:")
        print(x_comments.iloc[0]['Explicación'])

if __name__ == "__main__":
    main()
