package common_test

import (
	"Event-Scheduler/components/common"
	"Event-Scheduler/tests/utils"
	"testing"
)

func TestKeys(t *testing.T) {
	vector := []utils.TestCase[map[string]bool, []string]{
		{
			Name: "string keyed map",
			Input: map[string]bool{
				"key1": true,
				"key2": false,
			},
			Output: []string{"key1", "key2"},
		},
		{
			Name:   "empty map",
			Input:  map[string]bool{},
			Output: []string{},
		},
	}

	for _, v := range vector {
		output := common.Keys(v.Input)
		if !utils.ListEqual(v.Output, output) {
			t.Error(v.Error(output))
		}
	}
}

func TestSelectRandom(t *testing.T) {
	vector := []utils.TestCase[[]string, int]{
		{
			Name:   "2 choices",
			Input:  []string{"choice1", "choice2", "choice3"},
			Output: 2,
		},
		{
			Name:   "0 choices",
			Input:  []string{"choice1", "choice2", "choice3", "choice4"},
			Output: 0,
		},
	}

	for _, v := range vector {
		output := common.SelectRandom(v.Input, v.Output)
		if len(output) != v.Output {
			t.Error(v.Error(v.Output))
		}
	}
}

func TestWithout(t *testing.T) {
	vector := []utils.TestCase[struct {
		List    []string
		Without string
	}, []string]{
		{
			Name: "without 1",
			Input: struct {
				List    []string
				Without string
			}{
				List:    []string{"value1", "value2", "value3"},
				Without: "value2",
			},
			Output: []string{"value1", "value3"},
		},
		{
			Name: "without multiple",
			Input: struct {
				List    []string
				Without string
			}{
				List:    []string{"value1", "value1", "value3"},
				Without: "value1",
			},
			Output: []string{"value3"},
		},
		{
			Name: "without none",
			Input: struct {
				List    []string
				Without string
			}{
				List:    []string{"value1", "value2", "value3"},
				Without: "value4",
			},
			Output: []string{"value1", "value2", "value3"},
		},
	}

	for _, v := range vector {
		output := common.Without(v.Input.List, v.Input.Without)
		if !utils.ListEqual(output, v.Output) {
			t.Error(v.Error(output))
		}
	}
}

func TestIntersects(t *testing.T) {
	vector := []utils.TestCase[struct {
		L1 []string
		L2 []string
	}, bool]{
		{
			Name: "intersects 1",
			Input: struct {
				L1 []string
				L2 []string
			}{
				L1: []string{"value1", "value2", "value3"},
				L2: []string{"value2"},
			},
			Output: true,
		},
		{
			Name: "intersects 2",
			Input: struct {
				L1 []string
				L2 []string
			}{
				L1: []string{"value1", "value2", "value3"},
				L2: []string{"value3", "value2"},
			},
			Output: true,
		},
		{
			Name: "does not intersects 1",
			Input: struct {
				L1 []string
				L2 []string
			}{
				L1: []string{"value1", "value2", "value3"},
				L2: []string{"value4"},
			},
			Output: false,
		},
		{
			Name: "intersects 0",
			Input: struct {
				L1 []string
				L2 []string
			}{
				L1: []string{"value1", "value2", "value3"},
				L2: []string{},
			},
			Output: false,
		},
	}

	for _, v := range vector {
		if common.Intersects(v.Input.L1, v.Input.L2) != v.Output {
			t.Error(v.Error(!v.Output))
		}
	}
}

func TestUnorderedEqual(t *testing.T) {
	vector := []utils.TestCase[struct {
		L1 []string
		L2 []string
	}, bool]{
		{
			Name: "equal",
			Input: struct {
				L1 []string
				L2 []string
			}{
				L1: []string{"value1", "value2", "value3"},
				L2: []string{"value2", "value1", "value3"},
			},
			Output: true,
		},
		{
			Name: "unequal",
			Input: struct {
				L1 []string
				L2 []string
			}{
				L1: []string{"value1", "value2", "value3"},
				L2: []string{"value3", "value2", "value4"},
			},
			Output: false,
		},
		{
			Name: "different length",
			Input: struct {
				L1 []string
				L2 []string
			}{
				L1: []string{"value1", "value2", "value3"},
				L2: []string{"value1"},
			},
			Output: false,
		},
		{
			Name: "empty",
			Input: struct {
				L1 []string
				L2 []string
			}{
				L1: []string{},
				L2: []string{},
			},
			Output: true,
		},
	}

	for _, v := range vector {
		if common.UnorderedEqual(v.Input.L1, v.Input.L2) != v.Output {
			t.Error(v.Error(!v.Output))
		}
	}
}

func TestHasAdjacent(t *testing.T) {
	vector := []utils.TestCase[struct {
		List       []string
		Index      int
		Determiner func(string, bool) bool
	}, bool]{
		{
			Name: "has adjacent",
			Input: struct {
				List       []string
				Index      int
				Determiner func(string, bool) bool
			}{
				List:  []string{"value1", "value2", "value3"},
				Index: 1,
				Determiner: func(value string, above bool) bool {
					return value == "value3"
				},
			},
			Output: true,
		},
		{
			Name: "no adjacent",
			Input: struct {
				List       []string
				Index      int
				Determiner func(string, bool) bool
			}{
				List:  []string{"value1", "value2", "value3"},
				Index: 1,
				Determiner: func(value string, above bool) bool {
					return false
				},
			},
			Output: false,
		},
		{
			Name: "top",
			Input: struct {
				List       []string
				Index      int
				Determiner func(string, bool) bool
			}{
				List:  []string{"value1", "value2", "value3"},
				Index: 0,
				Determiner: func(value string, above bool) bool {
					return value == "value2"
				},
			},
			Output: true,
		},
		{
			Name: "bottom",
			Input: struct {
				List       []string
				Index      int
				Determiner func(string, bool) bool
			}{
				List:  []string{"value1", "value2", "value3"},
				Index: 2,
				Determiner: func(value string, above bool) bool {
					return value == "value2"
				},
			},
			Output: true,
		},
	}

	for _, v := range vector {
		output := common.HasAdjacent(
			v.Input.List,
			v.Input.Index,
			v.Input.Determiner,
		)
		if output != v.Output {
			t.Error(v.Error(output))
		}
	}
}
