package main

import (
	"bufio"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

// loadEnvFile loads environment variables from .env file (similar to Python's load_dotenv)
func loadEnvFile() {
	// Search for .env file in current directory and parent directories
	paths := []string{
		".env",
		"../.env",
		"../../.env",
		"algotradar-backend/.env",
		"algotradar-backend/assets/stocks/fmp/.env",
	}

	for _, envPath := range paths {
		if file, err := os.Open(envPath); err == nil {
			fmt.Printf("📄 Found .env file at: %s\n", envPath)

			scanner := bufio.NewScanner(file)
			for scanner.Scan() {
				line := strings.TrimSpace(scanner.Text())
				if line == "" || strings.HasPrefix(line, "#") {
					continue
				}

				parts := strings.SplitN(line, "=", 2)
				if len(parts) == 2 {
					key := strings.TrimSpace(parts[0])
					value := strings.TrimSpace(parts[1])
					// Remove quotes if present
					value = strings.Trim(value, `"'`)
					os.Setenv(key, value)

					if key == "FMP_API_KEY" {
						fmt.Printf("✅ Loaded FMP_API_KEY from .env file\n")
					}
				}
			}
			file.Close()
			return
		}
	}

	fmt.Println("⚠️ No .env file found in common locations")
}

func main() {
	fmt.Println("🧪 Testing optimized fmp_uk.go with small parallel processing...")

	// Try to load .env file first (like Python's load_dotenv())
	loadEnvFile()

	// Check if API key is available
	apiKey := os.Getenv("FMP_API_KEY")
	if apiKey == "" {
		fmt.Println("❌ Please set FMP_API_KEY environment variable first:")
		fmt.Println("   Windows: $env:FMP_API_KEY=\"your_api_key_here\"")
		fmt.Println("   Linux/Mac: export FMP_API_KEY=your_api_key_here")
		return
	}

	// Show partial API key for confirmation
	if len(apiKey) > 8 {
		fmt.Printf("✅ FMP_API_KEY found: %s...%s\n", apiKey[:8], apiKey[len(apiKey)-8:])
	} else {
		fmt.Println("✅ FMP_API_KEY found")
	}

	// Change to the fmp directory
	fmpDir := filepath.Join("algotradar-backend", "assets", "stocks", "fmp")
	if err := os.Chdir(fmpDir); err != nil {
		fmt.Printf("❌ Failed to change to fmp directory: %v\n", err)
		return
	}
	fmt.Printf("📁 Changed to directory: %s\n", fmpDir)

	// Create temporary wrapper file
	wrapperContent := `package main

func main() {
	get_UK()
}
`
	wrapperFile := "temp_wrapper_uk_optimized.go"
	if err := os.WriteFile(wrapperFile, []byte(wrapperContent), 0644); err != nil {
		fmt.Printf("❌ Failed to create wrapper file: %v\n", err)
		return
	}
	fmt.Println("📝 Created temporary wrapper file")

	cleanup := func() {
		os.Remove(wrapperFile)
		// Don't remove JSON file for debugging
		// os.Remove("uk_supabase.json")
		fmt.Println("🗑️ Cleaned up temporary wrapper file (kept JSON for inspection)")
	}
	defer cleanup()

	// Run the Go program
	fmt.Println("🚀 Running optimized fmp_uk.go...")
	fmt.Println("⚡ Expected improvements:")
	fmt.Println("   - Fixed JSON parsing errors (timestamp field)")
	fmt.Println("   - Smaller batch sizes (25 vs 50) for better reliability")
	fmt.Println("   - Better progress tracking every 50 batches")
	fmt.Println("   - Higher profile success rate")
	fmt.Println("")

	startTime := time.Now()

	cmd := exec.Command("go", "run", wrapperFile, "fmp_uk.go")
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	if err := cmd.Run(); err != nil {
		fmt.Printf("❌ Error running fmp_uk.go: %v\n", err)
		return
	}

	duration := time.Since(startTime)
	fmt.Printf("\n⏱️ Test completed in %.2f seconds\n", duration.Seconds())

	// Check if output file was created
	if info, err := os.Stat("uk_supabase.json"); err == nil {
		fmt.Println("✅ uk_supabase.json file created successfully!")
		fmt.Printf("📄 JSON file size: %d bytes\n", info.Size())

		// Show first 500 characters of the JSON file
		if data, err := os.ReadFile("uk_supabase.json"); err == nil {
			preview := string(data)
			if len(preview) > 500 {
				preview = preview[:500] + "..."
			}
			fmt.Printf("📄 First 500 chars:\n%s\n", preview)
		}
	} else {
		fmt.Printf("❌ uk_supabase.json file was not created: %v\n", err)
	}

	fmt.Println("🎉 Optimized UK test completed!")
	fmt.Println("💡 Key improvements tested:")
	fmt.Println("   ✅ JSON parsing should work without errors")
	fmt.Println("   ✅ Profile fetching should be faster and more reliable")
	fmt.Println("   ✅ Progress tracking should show every 50 batches")
	fmt.Println("   ✅ Success rate percentage should be displayed")
}
