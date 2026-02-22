$screens = @{
    "src/designs/Screen1.html" = "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ7Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpaCiVodG1sX2I2ZmIwOWU3ZDgzYzQ3YTliMGRlMWE2NWJjNjk5NGEzEgsSBxDsmrW13AUYAZIBIwoKcHJvamVjdF9pZBIVQhM0NTM1NzQ5NzkzOTU5MDk0MzY1&filename=&opi=89354086"
    "src/designs/Screen2.html" = "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ7Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpaCiVodG1sX2IzYjg2ZDI4NmEzOTQ3OTlhN2Y5M2U3NjI0ZWQ4OTRjEgsSBxDsmrW13AUYAZIBIwoKcHJvamVjdF9pZBIVQhM0NTM1NzQ5NzkzOTU5MDk0MzY1&filename=&opi=89354086"
    "src/designs/Screen3.html" = "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ7Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpaCiVodG1sXzYxOGI0NjUwMzAyNDQ2MjViYThjNTY1MThkOGZmYTk3EgsSBxDsmrW13AUYAZIBIwoKcHJvamVjdF9pZBIVQhM0NTM1NzQ5NzkzOTU5MDk0MzY1&filename=&opi=89354086"
    "src/designs/Screen4.html" = "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ7Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpaCiVodG1sXzAxMGZmMDVlY2RiODRiNGNiNDEwZDAzMWYwMzE4YjdiEgsSBxDsmrW13AUYAZIBIwoKcHJvamVjdF9pZBIVQhM0NTM1NzQ5NzkzOTU5MDk0MzY1&filename=&opi=89354086"
    "src/designs/Screen5.html" = "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ7Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpaCiVodG1sXzhkMTUyYjE2MzUwYTQzMzk4ZjkyZWNjZDFiOTcxOGIxEgsSBxDsmrW13AUYAZIBIwoKcHJvamVjdF9pZBIVQhM0NTM1NzQ5NzkzOTU5MDk0MzY1&filename=&opi=89354086"
    "src/designs/Screen6.html" = "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ7Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpaCiVodG1sXzdhMjhlOGM2YzQ5MjQyMzg4YjcwZTk0YTM0Yjk5NGZhEgsSBxDsmrW13AUYAZIBIwoKcHJvamVjdF9pZBIVQhM0NTM1NzQ5NzkzOTU5MDk0MzY1&filename=&opi=89354086"
    "src/designs/Screen7.html" = "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ7Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpaCiVodG1sXzBiYTk4Y2FkOTQ0NzQ4NGNiOTYxOWYwODkyMjc5NWE3EgsSBxDsmrW13AUYAZIBIwoKcHJvamVjdF9pZBIVQhM0NTM1NzQ5NzkzOTU5MDk0MzY1&filename=&opi=89354086"
    "src/designs/Screen8.html" = "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ7Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpaCiVodG1sX2M5NDM1ZmZjMjRlNjQyMmU4ODNiMzg0ZjA4YTE0M2JjEgsSBxDsmrW13AUYAZIBIwoKcHJvamVjdF9pZBIVQhM0NTM1NzQ5NzkzOTU5MDk0MzY1&filename=&opi=89354086"
}

foreach ($item in $screens.GetEnumerator()) {
    $path = $item.Key
    $url = $item.Value
    Write-Host "Downloading $path..."
    Invoke-WebRequest -Uri $url -OutFile $path
}
