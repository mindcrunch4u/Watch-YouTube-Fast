from langchain_text_splitters import RecursiveCharacterTextSplitter
from configuration import default_config

default_chunk_size=default_config.large_file_chunk_size

text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    model_name="gpt-4",
    chunk_size=default_chunk_size,
    chunk_overlap=1,
)

def large_text_to_list(large_text):
    texts = text_splitter.split_text(large_text)
    return texts

def main():

    testfile = "./state_of_the_union.txt"
    filecontent = None
    with open(testfile) as f:
        filecontent = f.read()

    texts = large_text_to_list(filecontent)
    print(texts[0])

if __name__ == "__main__":
    main()
