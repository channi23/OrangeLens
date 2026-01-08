"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const index_1 = require("../src/index");
async function main() {
    const baseUrl = process.env.PRAMANA_BASE_URL || "http://localhost:8000";
    const client = new index_1.PramanaClient({ baseUrl });
    const result = await client.verify({
        content_type: "text",
        text: "Breaking: scientists discover water on Mars again",
    });
    console.log("cached:", result.cached);
    console.log("proof:", result.proof);
}
main().catch((err) => {
    console.error(err);
    process.exit(1);
});
