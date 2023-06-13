import os
import nltk.data


def build_dataset(dataset_path, DOC_PATH_OR_LINK):
    if not os.path.exists(dataset_path):
        os.mkdir(dataset_path)
    tokenizer = nltk.data.load("tokenizers/punkt/english.pickle")
    i = 0
    docs_to_parts_dict = {}
    for filepath in DOC_PATH_OR_LINK:
        with open(filepath, "r") as f:
            list_files = []
            buf = ""
            data = f.read()
            data = tokenizer.tokenize(data)

            for item in data:
                buf += item
                words = buf.split(" ")
                if len(words) > 100:
                    i += 1
                    new_f = dataset_path + str(i) + ".txt"
                    with open(
                        new_f, "w"
                    ) as f_out:  # think about this for downloaded = binary files
                        f_out.write(buf)
                    buf = ""
                    list_files.append(new_f)
        docs_to_parts_dict[filepath] = list_files  # todo: think about keys
    return docs_to_parts_dict