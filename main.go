package main

import (
	"bufio"
	"flag"
	"fmt"
	"os"
	"strings"
)

func MatchDocumentOpen(line string) bool {
	return strings.HasPrefix(line, "<doc ") && strings.HasSuffix(line, ">")
}

func MatchDocumentClose(line string) bool {
	return line == "</doc>"
}

func MatchParagraphOpen(line string) bool {
	return line == "<p>" || line == "<p heading=\"1\">" || line == "<p heading=\"yes\">"
}

func MatchParagraphClose(line string) bool {
	return line == "</p>"
}

func MatchSentenceOpen(line string) bool {
	return line == "<s>" || line == "<s hack=\"1\">"
}

func MatchSentenceClose(line string) bool {
	return line == "</s>"
}

func MatchGlueIndicate(line string) bool {
	return line == "<g/>" || line == "<g />"
}

func main() {
	i := flag.String("i", "", "Path to the input text file")
	o := flag.String("o", "", "Path to the output text file")
	n := flag.Int("n", 0, "Number of docs to parse")

	flag.Parse()

	if *i == "" {
		return
	}

	f, err := os.Open(*i)

	if err != nil {
		return
	}

	defer f.Close()

	if *o == "" {
		return
	}

	w, err := os.Create(*o)

	if err != nil {
		return
	}

	defer w.Close()

	s := bufio.NewScanner(f)
	b := bufio.NewWriter(w)

	var sentence []string
	var parsedDocs int

	containsTab := func(line string) bool {
		return strings.Contains(line, "\t")
	}

	state := [3]int{0, 0, 0}

	p := 0 // 16403105954

	skip := false

	for s.Scan() {
		p++

		line := s.Text()

		if skip {
			if !MatchDocumentOpen(line) {
				continue
			}

			state = [3]int{0, 0, 0}
			skip = false
		}

		if state[0] == 0 {
			if MatchDocumentOpen(line) {
				state[0] = p

				continue
			}

			fmt.Println(state, p, "Expected document open but got:", line)

			skip = true

			continue
		}

		if state[0] != 0 && state[1] == 0 {
			if MatchDocumentClose(line) {
				state[0] = 0

				_, _ = b.WriteString(strings.Join(sentence, " ") + "\n")

				sentence = []string{}

				parsedDocs++

				if *n != 0 && parsedDocs >= *n {
					break
				}

				continue
			}

			if MatchParagraphOpen(line) {
				state[1] = p

				continue
			}

			fmt.Println(state, p, "Expected document close or paragraph open but got:", line)

			skip = true

			continue
		}

		if state[0] != 0 && state[1] != 0 && state[2] == 0 {
			if MatchParagraphClose(line) {
				state[1] = 0

				continue
			}

			if MatchSentenceOpen(line) {
				state[2] = p

				continue
			}

			fmt.Println(state, p, "Expected paragraph close or sentence open but got:", line)

			skip = true

			continue
		}

		if !(state[0] < state[1] && state[1] < state[2]) {
			fmt.Println(state, p, "Invalid state")

			break
		}

		// line is either data, glue, or sentence close

		if MatchSentenceClose(line) {
			state[2] = 0

			// Zapiš větu do výstupu a vymaž buffer
			if len(sentence) > 0 {
				// Přidání nového řádku po každé větě
				_, _ = b.WriteString(strings.Join(sentence, " ") + "\n")
				sentence = []string{}
			}

			continue
		}

		if MatchGlueIndicate(line) {
			continue
		}

		if !containsTab(line) {
			skip = true

			continue
		}

		fields := strings.Fields(line)

		if len(fields) > 0 {
			// Přidání každého slova do bufferu (věty)
			sentence = append(sentence, fields[0])
		}
	}

	if err := s.Err(); err != nil {
		fmt.Println("Error reading file:", err)
	}

	// Zajistí zápis všech zbývajících vět na konec souboru
	b.Flush()
}
