import React, { useState } from 'react';
import { Button } from "~/components/ui/button";
import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    CardDescription,
    CardFooter,
} from "~/components/ui/card";
import { Input } from "~/components/ui/input";
import { Badge } from "~/components/ui/badge";
import { Loader2, ChevronDown, ChevronUp, Copy } from "lucide-react";

const SearchInterface = () => {
    const [input, setInput] = useState("");
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [searchTerm, setSearchTerm] = useState("");
    const [expandedCards, setExpandedCards] = useState(new Set());

    const handleInputChange = (event) => {
        setInput(event.target.value);
    };

    const toggleCard = (index) => {
        const newExpanded = new Set(expandedCards);
        if (newExpanded.has(index)) {
            newExpanded.delete(index);
        } else {
            newExpanded.add(index);
        }
        setExpandedCards(newExpanded);
    };

    const handleFormSubmit = async (event) => {
        event.preventDefault();
        setLoading(true);
        setError("");
        setSearchTerm(input);
        setExpandedCards(new Set());

        try {
            const response = await fetch("http://localhost:4000/run_miner", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ input }),
            });

            if (!response.ok) {
                throw new Error("Failed to fetch results");
            }

            const data = await response.json();
            setResults(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const formatFeatureValue = (value) => {
        return value === "Unknown" ? "Not specified" : value;
    };

    const copyUUID = async (uuid) => {
        try {
            await navigator.clipboard.writeText(uuid);
            // Could add a toast notification here
        } catch (err) {
            console.error('Failed to copy UUID:', err);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 p-8">
            <div className="max-w-4xl mx-auto space-y-8">
                <Card className="w-full">
                    <CardHeader>
                        <CardTitle className="text-2xl font-bold">TV Product Search</CardTitle>
                        <CardDescription>
                            Enter specifications like screen size, resolution, or price range
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleFormSubmit} className="space-y-4">
                            <div className="flex gap-4">
                                <Input
                                    placeholder="e.g., 55 inch 4K TV or Smart TV under 15000 TL"
                                    value={input}
                                    onChange={handleInputChange}
                                    className="flex-1"
                                />
                                <Button type="submit" disabled={loading}>
                                    {loading ? (
                                        <>
                                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                            Searching...
                                        </>
                                    ) : (
                                        "Search"
                                    )}
                                </Button>
                            </div>
                        </form>
                    </CardContent>
                </Card>

                {searchTerm && (
                    <div className="flex items-center gap-2">
                        <span className="text-sm text-gray-500">Showing results for:</span>
                        <Badge variant="secondary" className="text-sm">
                            {searchTerm}
                        </Badge>
                    </div>
                )}

                {error && (
                    <Card className="bg-red-50">
                        <CardContent className="text-red-600 p-4">{error}</CardContent>
                    </Card>
                )}

                <div className="grid gap-6">
                    {results.map((result, index) => (
                        <Card key={index} className="overflow-hidden hover:shadow-lg transition-shadow">
                            <div className="bg-gray-100 px-6 py-2 flex justify-between items-center">
                                <div className="text-sm text-gray-600 font-mono flex items-center gap-2">
                                    ID: {result.uuid}
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        className="h-6 w-6 p-0"
                                        onClick={() => copyUUID(result.uuid)}
                                    >
                                        <Copy className="h-4 w-4" />
                                    </Button>
                                </div>
                            </div>
                            <CardHeader className="cursor-pointer" onClick={() => toggleCard(index)}>
                                <div className="flex justify-between items-center">
                                    <div className="space-y-2">
                                        <CardTitle className="text-lg flex items-center gap-2">
                                            {result.marka} {result.model}
                                            <Badge
                                                variant={result.similarity > 80 ? "default" : "secondary"}
                                            >
                                                {result.similarity.toFixed(1)}% Match
                                            </Badge>
                                        </CardTitle>
                                        <div className="text-sm text-gray-600">
                                            {result.ekran_ebati} • {result.price}
                                        </div>
                                    </div>
                                    {expandedCards.has(index) ? (
                                        <ChevronUp className="h-6 w-6 text-gray-400" />
                                    ) : (
                                        <ChevronDown className="h-6 w-6 text-gray-400" />
                                    )}
                                </div>
                            </CardHeader>

                            {expandedCards.has(index) && (
                                <CardContent className="border-t">
                                    <div className="grid grid-cols-2 gap-4 py-2">
                                        <div>
                                            <p className="text-sm font-medium text-gray-500">Resolution</p>
                                            <p>{formatFeatureValue(result.cozunurluk)}</p>
                                        </div>
                                        <div>
                                            <p className="text-sm font-medium text-gray-500">Display Technology</p>
                                            <p>{formatFeatureValue(result.goruntu_teknolojisi)}</p>
                                        </div>
                                        <div>
                                            <p className="text-sm font-medium text-gray-500">Refresh Rate</p>
                                            <p>{formatFeatureValue(result.yenileme_hizi)}</p>
                                        </div>
                                        <div>
                                            <p className="text-sm font-medium text-gray-500">Smart TV</p>
                                            <p>{formatFeatureValue(result.smart_tv)}</p>
                                        </div>
                                        <div>
                                            <p className="text-sm font-medium text-gray-500">HDR</p>
                                            <p>{formatFeatureValue(result.hdr)}</p>
                                        </div>
                                        {result.additional_features && Object.entries(result.additional_features).map(([key, value]) => (
                                            <div key={key}>
                                                <p className="text-sm font-medium text-gray-500">
                                                    {key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
                                                </p>
                                                <p>{formatFeatureValue(value)}</p>
                                            </div>
                                        ))}
                                    </div>
                                </CardContent>
                            )}

                            <CardFooter className="bg-gray-50 flex justify-between items-center">
                                <a
                                    href={result.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-blue-600 hover:text-blue-800 text-sm"
                                >
                                    View on Hepsiburada →
                                </a>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={(e) => {
                                        e.preventDefault();
                                        toggleCard(index);
                                    }}
                                >
                                    {expandedCards.has(index) ? "Show Less" : "Show More"}
                                </Button>
                            </CardFooter>
                        </Card>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default SearchInterface;