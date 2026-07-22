package utils

import (
	"errors"
	"fmt"
)

type TestCase[I any, O any] struct {
	Name   string
	Input  I
	Output O
}

func (c TestCase[I, O]) Error(got O) error {
	return errors.New(fmt.Sprintf(
		"\"%v\" expected %v, got %v",
		c.Name, c.Output, got,
	))
}

func ListEqual[T comparable](l1 []T, l2 []T) bool {
	if len(l1) != len(l2) {
		return false
	}
	for i := range l1 {
		if l1[i] != l2[i] {
			return false
		}
	}
	return true
}
