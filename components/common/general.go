package common

import (
	"math/rand"
)

func Keys[K comparable, V any](m map[K]V) []K {
	keys := []K{}
	for k := range m {
		keys = append(keys, k)
	}
	return keys
}

func SelectRandom[T any](list []T, amount int) []T {
	pool := make([]T, len(list))
	copy(pool, list)
	if amount > len(pool) {
		panic("SelectRandom cannot choose more than the slice has to offer!")
	}
	values := []T{}
	for i := 0; i < amount; i++ {
		index := rand.Intn(len(pool))
		values = append(values, pool[index])
		pool = append(pool[0:index], pool[index+1:]...)
	}
	return values
}

func Without[T comparable](list []T, element T) []T {
	new := []T{}
	pool := make([]T, len(list))
	copy(pool, list)
	for _, e := range pool {
		if e != element {
			new = append(new, e)
		}
	}
	return new
}

func Intersects[T comparable](l1 []T, l2 []T) bool {
	pool := map[T]bool{}
	for _, e := range l1 {
		pool[e] = true
	}
	for _, e := range l2 {
		if pool[e] {
			return true
		}
	}
	return false
}

//compares two lists if they are equal regardless of order
func UnorderedEqual[T comparable](l1 []T, l2 []T) bool {
	if len(l1) != len(l2) {
		return false
	}

	m := map[T]bool{}
	for _, v := range l1 {
		m[v] = true
	}

	for _, v := range l2 {
		if !m[v] {
			return false
		}
	}

	return true
}

func HasAdjacent[T any](l []T, index int, determiner func(value T, above bool) bool) bool {
	if index > 0 {
		if determiner(l[index-1], true) {
			return true
		}
	}
	if index < len(l)-1 {
		if determiner(l[index+1], false) {
			return true
		}
	}
	return false
}
