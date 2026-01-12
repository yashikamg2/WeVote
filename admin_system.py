"""
Admin Voting System
Complete administrative interface for managing elections
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import random
import string
from datetime import datetime
from crypto_handler import CryptoHandler
from config_manager import ConfigManager


class AdminVotingSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Admin Voting System - v1.0")
        self.root.geometry("950x750")
        self.root.configure(bg="#f0f0f0")
        
        # Initialize managers
        self.crypto = CryptoHandler()
        self.config_manager = ConfigManager()
        
        # State variables
        self.candidates = []
        self.session_code = None
        self.encryption_key = None
        self.is_election_active = False
        
        self.setup_ui()
        self.load_existing_election()
    
    def setup_ui(self):
        """Setup the complete UI"""
        # Title Bar
        title_frame = tk.Frame(self.root, bg="#2c3e50", height=90)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text="🗳️ ADMIN VOTING SYSTEM", 
                              font=("Arial", 26, "bold"), fg="white", bg="#2c3e50")
        title_label.pack(pady=25)
        
        # Main container with scrollbar
        main_canvas = tk.Canvas(self.root, bg="#f0f0f0")
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=main_canvas.yview)
        self.main_frame = tk.Frame(main_canvas, bg="#f0f0f0")
        
        self.main_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=self.main_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        main_canvas.pack(side="left", fill="both", expand=True, padx=20, pady=20)
        scrollbar.pack(side="right", fill="y")
        
        # Build sections
        self.build_candidate_section()
        self.build_election_control_section()
        self.build_monitoring_section()
        self.build_results_section()
    
    def build_candidate_section(self):
        """Build candidate management section"""
        frame = tk.LabelFrame(self.main_frame, text="📋 Candidate Management", 
                             font=("Arial", 13, "bold"), bg="white", 
                             padx=25, pady=20, relief=tk.GROOVE, bd=2)
        frame.pack(fill=tk.X, pady=(0, 15))
        
        # Entry row
        entry_frame = tk.Frame(frame, bg="white")
        entry_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(entry_frame, text="Candidate Name:", font=("Arial", 11), 
                bg="white").pack(side=tk.LEFT, padx=(0, 10))
        
        self.candidate_entry = tk.Entry(entry_frame, font=("Arial", 11), width=35)
        self.candidate_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.candidate_entry.bind('<Return>', lambda e: self.add_candidate())
        
        tk.Button(entry_frame, text="➕ Add", command=self.add_candidate,
                 bg="#27ae60", fg="white", font=("Arial", 10, "bold"), 
                 padx=20, pady=6, cursor="hand2").pack(side=tk.LEFT)
        
        # Candidates list
        list_frame = tk.Frame(frame, bg="white")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(list_frame, text="Candidates List:", font=("Arial", 11, "bold"), 
                bg="white").pack(anchor=tk.W, pady=(0, 8))
        
        list_container = tk.Frame(list_frame, bg="white")
        list_container.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.candidates_listbox = tk.Listbox(list_container, font=("Arial", 11), 
                                            height=6, yscrollcommand=scrollbar.set)
        self.candidates_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.candidates_listbox.yview)
        
        # Buttons row
        btn_frame = tk.Frame(frame, bg="white")
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Button(btn_frame, text="🗑️ Remove Selected", command=self.remove_candidate,
                 bg="#e74c3c", fg="white", font=("Arial", 9, "bold"), 
                 padx=15, pady=5, cursor="hand2").pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(btn_frame, text="🔄 Clear All", command=self.clear_candidates,
                 bg="#95a5a6", fg="white", font=("Arial", 9, "bold"), 
                 padx=15, pady=5, cursor="hand2").pack(side=tk.LEFT)
    
    def build_election_control_section(self):
        """Build election control section"""
        frame = tk.LabelFrame(self.main_frame, text="⚙️ Election Control", 
                             font=("Arial", 13, "bold"), bg="white", 
                             padx=25, pady=20, relief=tk.GROOVE, bd=2)
        frame.pack(fill=tk.X, pady=(0, 15))
        
        # Start button
        self.start_btn = tk.Button(frame, text="🚀 START ELECTION", 
                                   command=self.initialize_election,
                                   bg="#3498db", fg="white", 
                                   font=("Arial", 13, "bold"), 
                                   padx=40, pady=12, cursor="hand2")
        self.start_btn.pack(pady=(0, 15))
        
        # Session info
        self.session_frame = tk.Frame(frame, bg="#ecf0f1", relief=tk.SOLID, bd=1)
        self.session_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.session_label = tk.Label(self.session_frame, text="No active election", 
                                     font=("Arial", 14, "bold"), bg="#ecf0f1", 
                                     fg="#7f8c8d", pady=15)
        self.session_label.pack()
        
        # Stop button
        self.stop_btn = tk.Button(frame, text="⏹️ End Election", 
                                 command=self.end_election,
                                 bg="#e67e22", fg="white", 
                                 font=("Arial", 11, "bold"), 
                                 padx=30, pady=8, cursor="hand2", 
                                 state=tk.DISABLED)
        self.stop_btn.pack()
    
    def build_monitoring_section(self):
        """Build vote monitoring section"""
        frame = tk.LabelFrame(self.main_frame, text="📊 Live Monitoring", 
                             font=("Arial", 13, "bold"), bg="white", 
                             padx=25, pady=20, relief=tk.GROOVE, bd=2)
        frame.pack(fill=tk.X, pady=(0, 15))
        
        info_frame = tk.Frame(frame, bg="white")
        info_frame.pack(fill=tk.X)
        
        self.votes_count_label = tk.Label(info_frame, text="Votes Received: 0", 
                                         font=("Arial", 12, "bold"), bg="white")
        self.votes_count_label.pack(side=tk.LEFT, padx=(0, 20))
        
        tk.Button(info_frame, text="🔄 Refresh", command=self.refresh_vote_count,
                 bg="#16a085", fg="white", font=("Arial", 9, "bold"), 
                 padx=15, pady=5, cursor="hand2").pack(side=tk.LEFT)
    
    def build_results_section(self):
        """Build results section"""
        frame = tk.LabelFrame(self.main_frame, text="🏆 Election Results", 
                             font=("Arial", 13, "bold"), bg="white", 
                             padx=25, pady=20, relief=tk.GROOVE, bd=2)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Control buttons
        btn_frame = tk.Frame(frame, bg="white")
        btn_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Button(btn_frame, text="🔓 Decrypt & Count Votes", 
                 command=self.decrypt_and_count,
                 bg="#9b59b6", fg="white", font=("Arial", 12, "bold"), 
                 padx=25, pady=10, cursor="hand2").pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(btn_frame, text="💾 Export Results", 
                 command=self.export_results,
                 bg="#34495e", fg="white", font=("Arial", 10, "bold"), 
                 padx=20, pady=8, cursor="hand2").pack(side=tk.LEFT)
        
        # Results display
        self.results_text = scrolledtext.ScrolledText(frame, font=("Consolas", 10), 
                                                     height=15, wrap=tk.WORD,
                                                     bg="#f8f9fa")
        self.results_text.pack(fill=tk.BOTH, expand=True)
        self.results_text.insert(tk.END, "No results yet. Start an election and decrypt votes to see results.")
    
    def add_candidate(self):
        """Add a candidate to the list"""
        name = self.candidate_entry.get().strip()
        
        if not name:
            messagebox.showwarning("Warning", "Please enter a candidate name!")
            return
        
        if name in self.candidates:
            messagebox.showwarning("Warning", "This candidate already exists!")
            return
        
        if self.is_election_active:
            messagebox.showerror("Error", "Cannot add candidates during active election!")
            return
        
        self.candidates.append(name)
        self.candidates_listbox.insert(tk.END, name)
        self.candidate_entry.delete(0, tk.END)
        self.candidate_entry.focus()
    
    def remove_candidate(self):
        """Remove selected candidate"""
        selection = self.candidates_listbox.curselection()
        
        if not selection:
            messagebox.showwarning("Warning", "Please select a candidate to remove!")
            return
        
        if self.is_election_active:
            messagebox.showerror("Error", "Cannot remove candidates during active election!")
            return
        
        idx = selection[0]
        candidate = self.candidates_listbox.get(idx)
        self.candidates.remove(candidate)
        self.candidates_listbox.delete(idx)
    
    def clear_candidates(self):
        """Clear all candidates"""
        if self.is_election_active:
            messagebox.showerror("Error", "Cannot clear candidates during active election!")
            return
        
        if not self.candidates:
            return
        
        if messagebox.askyesno("Confirm", "Clear all candidates?"):
            self.candidates.clear()
            self.candidates_listbox.delete(0, tk.END)
    
    def initialize_election(self):
        """Initialize and start election"""
        if len(self.candidates) < 2:
            messagebox.showerror("Error", "Please add at least 2 candidates!")
            return
        
        # Generate session code
        self.session_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        # Generate encryption key
        self.encryption_key = self.crypto.generate_key()
        key_string = self.crypto.key_to_string(self.encryption_key)
        
        # Save configuration
        self.config_manager.save_election_config(self.session_code, self.candidates, key_string)
        
        # Update UI
        self.is_election_active = True
        self.session_label.config(
            text=f"🔑 SESSION CODE: {self.session_code}\n"
                 f"Share this code with all voters!",
            fg="#27ae60", bg="#d5f4e6"
        )
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        messagebox.showinfo("Election Started!", 
                          f"Election has been initialized!\n\n"
                          f"Session Code: {self.session_code}\n\n"
                          f"Share this code with all voters.\n"
                          f"They will need the 'election_config.json' file.")
    
    def end_election(self):
        """End the current election"""
        if messagebox.askyesno("Confirm", "End the current election?"):
            self.is_election_active = False
            self.session_label.config(
                text=f"Election Ended - Code: {self.session_code}",
                fg="#e74c3c", bg="#fadbd8"
            )
            self.stop_btn.config(state=tk.DISABLED)
            messagebox.showinfo("Election Ended", "You can now count the votes.")
    
    def refresh_vote_count(self):
        """Refresh the vote count display"""
        count = self.config_manager.get_vote_count()
        self.votes_count_label.config(text=f"Votes Received: {count}")
    
    def decrypt_and_count(self):
        """Decrypt all votes and count results"""
        if not self.session_code:
            messagebox.showerror("Error", "No election has been initialized!")
            return
        
        # Load configuration
        config = self.config_manager.load_election_config()
        if not config:
            messagebox.showerror("Error", "Election configuration not found!")
            return
        
        key = self.crypto.string_to_key(config["key"])
        
        # Initialize vote counts
        vote_counts = {candidate: 0 for candidate in self.candidates}
        total_votes = 0
        invalid_votes = 0
        
        # Load and decrypt all votes
        votes = self.config_manager.load_all_votes()
        
        for filename, encrypted_data in votes:
            try:
                vote_data = self.crypto.decrypt_vote(encrypted_data, key)
                
                if vote_data["session_code"] == self.session_code:
                    candidate = vote_data["vote"]
                    if candidate in vote_counts:
                        vote_counts[candidate] += 1
                        total_votes += 1
                else:
                    invalid_votes += 1
            
            except Exception as e:
                invalid_votes += 1
                print(f"Error processing {filename}: {e}")
        
        # Save results
        self.config_manager.save_results(self.session_code, total_votes, vote_counts)
        
        # Display results
        self.display_results(vote_counts, total_votes, invalid_votes)
    
    def display_results(self, vote_counts, total_votes, invalid_votes):
        """Display formatted results"""
        self.results_text.delete(1.0, tk.END)
        
        # Header
        self.results_text.insert(tk.END, "="*70 + "\n")
        self.results_text.insert(tk.END, " "*20 + "ELECTION RESULTS\n")
        self.results_text.insert(tk.END, "="*70 + "\n\n")
        
        self.results_text.insert(tk.END, f"Session Code: {self.session_code}\n")
        self.results_text.insert(tk.END, f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        self.results_text.insert(tk.END, f"Total Valid Votes: {total_votes}\n")
        if invalid_votes > 0:
            self.results_text.insert(tk.END, f"Invalid Votes: {invalid_votes}\n")
        self.results_text.insert(tk.END, "\n" + "="*70 + "\n\n")
        
        # Sort results
        sorted_results = sorted(vote_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Display each candidate
        for i, (candidate, votes) in enumerate(sorted_results, 1):
            percentage = (votes / total_votes * 100) if total_votes > 0 else 0
            
            self.results_text.insert(tk.END, f"Rank {i}: {candidate}\n")
            self.results_text.insert(tk.END, f"       Votes: {votes} ({percentage:.2f}%)\n")
            self.results_text.insert(tk.END, f"       {'█' * int(percentage/2)}\n\n")
        
        # Winner declaration
        if sorted_results and sorted_results[0][1] > 0:
            winner = sorted_results[0][0]
            winner_votes = sorted_results[0][1]
            
            self.results_text.insert(tk.END, "="*70 + "\n")
            self.results_text.insert(tk.END, f"{'🏆 WINNER 🏆':^70}\n")
            self.results_text.insert(tk.END, f"{winner:^70}\n")
            self.results_text.insert(tk.END, f"{'with ' + str(winner_votes) + ' votes':^70}\n")
            self.results_text.insert(tk.END, "="*70 + "\n")
        
        messagebox.showinfo("Success", 
                          f"Results calculated successfully!\n\n"
                          f"Total votes: {total_votes}\n"
                          f"Winner: {sorted_results[0][0] if sorted_results else 'N/A'}")
    
    def export_results(self):
        """Export results to a text file"""
        content = self.results_text.get(1.0, tk.END)
        
        if "No results yet" in content:
            messagebox.showwarning("Warning", "No results to export!")
            return
        
        filename = f"results_{self.session_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(filename, 'w') as f:
            f.write(content)
        
        messagebox.showinfo("Exported", f"Results exported to:\n{filename}")
    
    def load_existing_election(self):
        """Load existing election if available"""
        config = self.config_manager.load_election_config()
        
        if config:
            self.session_code = config["session_code"]
            self.candidates = config["candidates"]
            
            for candidate in self.candidates:
                self.candidates_listbox.insert(tk.END, candidate)
            
            if config.get("status") == "active":
                self.is_election_active = True
                self.session_label.config(
                    text=f"🔑 SESSION CODE: {self.session_code}\n"
                         f"(Loaded from previous session)",
                    fg="#f39c12", bg="#fef5e7"
                )
                self.start_btn.config(state=tk.DISABLED)
                self.stop_btn.config(state=tk.NORMAL)
            
            self.refresh_vote_count()


def main():
    root = tk.Tk()
    app = AdminVotingSystem(root)
    root.mainloop()


if __name__ == "__main__":
    main()
