import os

file_path = "resum_format.pdf"
file_text = os.path.splitext(file_path)[1].lower()

class ResumeParser:
    def __init__(self):
        self.supported_formats = ['.pdf','.docx']
    
    def parse(self, file_path: str) -> dict:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_text = os.path.splitext(file_path)[1].lower()
        
        if file_text not in self.supported_formats:
            raise ValueError(f"Unsupported file formar:{file_text}")

if __name__ == "__main__":
    # parser = ResumeParser()
    
    # file_path = "resum_format.df"
    # parser.parse(file_path)
    import re
    from sklearn.feature_extraction.text import CountVectorizer
    
    def clean(text):
        text = text.lower()
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        return text

    texts = "Hello, World! This is a Test. Resume #1: John Doe's Resume/)."
    cleaned_text = clean(texts)
    print(cleaned_text)
    vectorizer = CountVectorizer()
    X = vectorizer.fit_transform([cleaned_text])
    print(X.toarray())
    from sklearn.feature_extraction.text import TfidfVectorizer
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform([cleaned_text])
    
    from sklearn.model_selection import train_test_split
    from sklearn.linear_model import LogisticRegression

    X_train, X_test, y_train, y_test = train_test_split(X, labels)

    model = LogisticRegression()
    model.fit(X_train, y_train)
    from sklearn.metrics import accuracy_score

    pred = model.predict(X_test)
    print(accuracy_score(y_test, pred))
    new = vectorizer.transform(["I hate this"])
    print(model.predict(new))
    
    
    
    
        
        